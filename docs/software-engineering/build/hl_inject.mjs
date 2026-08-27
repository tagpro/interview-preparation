// Syntax-highlight every <pre> block in the built pages with TanStack Highlight.
//
// Highlighting happens HERE, at build time -- the pages ship plain <span> markup
// and a small block of CSS, and load no highlighter at runtime. That keeps the
// artifact CSP untouched (no external script, no inline color styles) and costs
// the reader nothing.
//
// Runs over finished HTML rather than the fragments, like gloss_inject.py, so one
// pass covers all seven pages. Re-runnable: it strips the spans it previously
// wrote and re-derives them, so run it after any rebuild.
//
//     node hl_inject.mjs             # all pages
//     node hl_inject.mjs --check     # report only, write nothing
import fs from 'node:fs';
import { createHighlighter, renderTokens, renderNodesToHtml } from '@tanstack/highlight/core';
import { createThemeRule } from '@tanstack/highlight/theme';
import { python } from '@tanstack/highlight/languages/python';
import { sql } from '@tanstack/highlight/languages/sql';
import { yaml } from '@tanstack/highlight/languages/yaml';
import { toml } from '@tanstack/highlight/languages/toml';
import { json } from '@tanstack/highlight/languages/json';
import { html } from '@tanstack/highlight/languages/html';
import { http } from '@tanstack/highlight/languages/http';
import { dockerfile } from '@tanstack/highlight/languages/dockerfile';
import { env } from '@tanstack/highlight/languages/env';
import { markdown } from '@tanstack/highlight/languages/markdown';
import { plaintext } from '@tanstack/highlight/languages/plaintext';
import { go, java, gomod, hcl, consoleLang, withCodas } from './hl_langs.mjs';
import { PAGES, detect } from './hl_detect.mjs';
import { lightTheme, darkTheme } from './hl_theme.mjs';

const OPEN = '<!-- highlight -->', CLOSE = '<!-- /highlight -->';
const GLOSS = '<!-- glossary -->';
const CHECK = process.argv.includes('--check');

const highlighter = createHighlighter({
  fallbackLanguage: 'plaintext',
  languages: [go, java, gomod, hcl, consoleLang, python, sql, yaml, toml, json,
              html, http, dockerfile, env, markdown, plaintext].map(withCodas),
});

// The <pre> bodies are HTML-escaped source. Decode before tokenizing; the
// renderer re-escapes. &larr;/&rarr;/&rsquo; appear inside code comments and
// come back as the literal characters, which render identically.
const ENT = { lt: '<', gt: '>', amp: '&', quot: '"', apos: "'", '#39': "'",
              larr: '←', rarr: '→', rsquo: '’', mdash: '—', ndash: '–', nbsp: ' ' };
const decode = s => s.replace(/&(#39|#x27|lt|gt|amp|quot|apos|larr|rarr|rsquo|mdash|ndash|nbsp);/g,
  (_, k) => ENT[k === '#x27' ? '#39' : k]);
const text = frag => decode(frag.replace(/<[^>]+>/g, ''));

function themeCss() {
  const vars = t => createThemeRule('SEL', t).replace(/^SEL \{\n|\n\}$/g, '')
    .split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('--th-background'))
    .join('');
  const classes = Object.keys(lightTheme.tokens)
    .map(k => `pre .th-${k}{color:var(--th-${k})}`).join('');
  return [
    OPEN,
    '<style>',
    `:root{${vars(lightTheme)}}`,
    `@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){${vars(darkTheme)}}}`,
    `:root[data-theme="dark"]{${vars(darkTheme)}}`,
    classes,
    '</style>',
    CLOSE,
  ].join('\n');
}

// The three passes all splice a block in ahead of the next marker, and each one
// leaves its own idea of the blank line before it. Left alone they leapfrog and
// the file grows a newline per full run. Normalising the gap here -- in all
// three passes, identically -- makes the composition converge.
const tidy = t => t.replace(/\n{2,}(?=<!-- \/?(?:highlight|print|glossary) -->)/g, '\n');

const RE = /<pre([^>]*)>([\s\S]*?)<\/pre>/g;
let totals = {}, blocks = 0, failures = 0;

for (const page of PAGES) {
  let s = fs.readFileSync(page, 'utf8');
  let n = 0, changed = 0;

  s = s.replace(RE, (whole, attrs, body) => {
    n++;
    const code = text(body);
    const lang = detect(body, attrs, page);
    totals[lang] = (totals[lang] || 0) + 1;
    const out = renderNodesToHtml(renderTokens(highlighter.highlight(code, { lang }).tokens));
    // The code text must survive the round trip exactly.
    if (text(out) !== code) {
      failures++;
      console.error(`MISMATCH ${page} #${n} (${lang})`);
      return whole;
    }
    if (out !== body) changed++;
    return `<pre${attrs}>${out}</pre>`;
  });
  blocks += n;

  // Splice the theme CSS in, replacing any block from a previous run. Sits
  // before the glossary block so gloss_inject.py can still be re-run after.
  // Pages with no code at all (the two prose pillars) get nothing.
  if (n === 0 && !s.includes(OPEN)) {
    console.log(`${page.padEnd(26)}   0 blocks, no code -- skipped`);
    continue;
  }
  if (s.includes(OPEN)) {
    const tail = s.indexOf(CLOSE) + CLOSE.length;
    s = s.slice(0, s.indexOf(OPEN)) + s.slice(s[tail] === '\n' ? tail + 1 : tail);
  }
  const css = themeCss() + '\n';
  s = s.includes(GLOSS) ? s.replace(GLOSS, css + GLOSS) : s.replace(/\n*$/, '\n') + css;

  if (!CHECK) fs.writeFileSync(page, tidy(s));
  console.log(`${page.padEnd(26)} ${String(n).padStart(3)} blocks, ${String(changed).padStart(3)} rewritten`);
}
console.log(`\n${blocks} blocks total`, JSON.stringify(totals));
console.log(failures ? `${failures} ROUND-TRIP FAILURES` : 'round-trip: all blocks byte-identical');
process.exit(failures ? 1 : 0);
