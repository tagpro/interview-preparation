// Self-host the site's fonts, so nothing on it needs the network.
//
// The pages link Google Fonts, which is the only external resource the served
// site loads. This fetches the same faces, keeps only the unicode subsets the
// pages actually use, and writes a stylesheet whose url()s resolve relative to
// itself -- so one copy serves every page whatever its depth, from a web server
// or straight off disk.
//
//     node fonts_local.mjs <site-root> <out-dir>
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const SITE = path.resolve(process.argv[2] || '.');
const OUT = path.resolve(process.argv[3] || path.join(SITE, 'fonts'));

const HREF = 'https://fonts.googleapis.com/css2' +
  '?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800' +
  '&family=IBM+Plex+Sans:wght@400;500;600' +
  '&family=IBM+Plex+Mono:wght@400;500;600&display=swap';
// Google serves woff2 only to a user agent that says it can take it.
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';

// --- 1. which characters does the site actually render ---------------------
// Counted from the rendered DOM, not the source: the pages are written with
// HTML entities, and several glyphs (the contents tick, the run marker) exist
// only as CSS generated content. Both have to be counted or a subset the site
// needs gets dropped as unused.
function pages(dir, acc = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { if (e.name !== 'fonts' && e.name !== 'build') pages(p, acc); }
    else if (e.name.endsWith('.html')) acc.push(p);
  }
  return acc;
}
const files = pages(SITE);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const used = new Set();
for (const f of files) {
  const page = await browser.newPage();
  await page.goto('file://' + f, { waitUntil: 'load' });
  await page.waitForTimeout(300);          // let the glossary pass wrap its terms
  const chars = await page.evaluate(() => {
    const out = new Set();
    const add = t => { for (const ch of t || '') out.add(ch.codePointAt(0)); };
    const w = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      const tag = n.parentNode && n.parentNode.nodeName;
      if (tag !== 'SCRIPT' && tag !== 'STYLE') add(n.nodeValue);
    }
    for (const el of document.querySelectorAll('*'))
      for (const pseudo of ['::before', '::after']) {
        const c = getComputedStyle(el, pseudo).content;
        if (c && c !== 'none' && c !== 'normal') add(c.replace(/^"|"$/g, ''));
      }
    return [...out];
  });
  chars.forEach(c => used.add(c));
  await page.close();
}
await browser.close();
const nonAscii = [...used].filter(c => c > 127).sort((a, b) => a - b);
console.log(`${files.length} pages, ${used.size} distinct codepoints rendered ` +
  `(${nonAscii.length} non-ASCII: ${nonAscii.map(c => String.fromCodePoint(c)).join('')})`);

// --- 2. the upstream stylesheet ---------------------------------------------
const css = await (await fetch(HREF, { headers: { 'User-Agent': UA } })).text();

const BLOCK = /\/\*\s*([\w\[\]-]+)\s*\*\/\s*(@font-face\s*\{[^}]*\})/g;
const blocks = [];
for (const m of css.matchAll(BLOCK)) {
  const body = m[2];
  const get = k => (body.match(new RegExp(k + ':\\s*([^;]+);'))?.[1] ?? '').trim();
  const ranges = get('unicode-range').split(',').map(r => {
    const [a, b] = r.trim().replace(/^U\+/i, '').split('-');
    const lo = parseInt(a.replace(/\?/g, '0'), 16);
    const hi = parseInt((b ?? a).replace(/\?/g, 'F'), 16);
    return [lo, hi];
  });
  blocks.push({
    subset: m[1], body,
    family: get('font-family').replace(/['"]/g, ''),
    weight: get('font-weight'),
    url: body.match(/url\((https:[^)]+)\)/)[1],
    ranges,
  });
}

// --- 3. keep the subsets the site needs -------------------------------------
const keep = blocks.filter(b => b.ranges.some(([lo, hi]) =>
  [...used].some(c => c >= lo && c <= hi)));
const dropped = blocks.length - keep.length;

// --- 4. download and write ---------------------------------------------------
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
let bytes = 0;
const rules = [];
for (const b of keep) {
  const name = `${slug(b.family)}-${b.weight}-${slug(b.subset)}.woff2`;
  const buf = Buffer.from(await (await fetch(b.url)).arrayBuffer());
  fs.writeFileSync(path.join(OUT, name), buf);
  bytes += buf.length;
  rules.push(`/* ${b.subset} */\n` + b.body.replace(/url\(https:[^)]+\)/, `url(${name})`));
}
fs.writeFileSync(path.join(OUT, 'fonts.css'),
  `/* The site's fonts, served from here rather than from Google, so that nothing\n` +
  `   on the site needs the network. Generated by build/fonts_local.mjs -- the\n` +
  `   subsets kept are the ones the pages' own text uses.\n\n` +
  `   url()s are relative to this file, so one copy serves every page whatever\n` +
  `   its depth, from a server or straight off disk. */\n\n` +
  rules.join('\n\n') + '\n');

const families = [...new Set(keep.map(b => b.family))];
console.log(`kept ${keep.length} faces (${dropped} subsets dropped as unused), ` +
  `${(bytes / 1024).toFixed(0)} KB`);
console.log(`families: ${families.join(', ')}`);
console.log(`subsets:  ${[...new Set(keep.map(b => b.subset))].join(', ')}`);
console.log(`-> ${path.relative(process.cwd(), OUT)}/fonts.css`);
