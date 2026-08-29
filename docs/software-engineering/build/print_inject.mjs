// Give every page a print stylesheet.
//
// One <style> block per page, spliced in ahead of the glossary marker like the
// highlight pass, so gloss_inject.py can still be re-run after it. Re-runnable:
// it removes its own previous block rather than stacking a second one.
//
// The palette comes from print_theme.mjs, which derives from hl_theme.mjs, so
// the screen and print token sets cannot drift apart.
//
//     node print_inject.mjs             # all pages
//     node print_inject.mjs --check     # report only, write nothing
import fs from 'node:fs';
import { PAGES } from './hl_detect.mjs';
import { printTheme, seriesTokens } from './print_theme.mjs';

const OPEN = '<!-- print -->', CLOSE = '<!-- /print -->';
const GLOSS = '<!-- glossary -->';
const CHECK = process.argv.includes('--check');

// Every token the pages read, pinned to its print value. !important because the
// dark values live behind :root:not([data-theme="light"]), which outranks :root.
function tokens() {
  const one = (k, v) => `--${k}:${v}!important;`;
  return [
    ...Object.entries(seriesTokens).map(([k, v]) => one(k, v)),
    ...Object.entries(printTheme.tokens).map(([k, v]) => one(`th-${k}`, v)),
  ].join('');
}

// The AWS page's snippets come in Go and Python and one is hidden at any time.
// Printing follows what is on screen, which is right -- but the switch that
// says which is which is in the top bar, and the top bar does not print.
const AWS = `
  /* which half of the AWS page this copy is */
  .langnote { display: none; }
  .hero .lede::after {
    display: block; margin-top: 14pt; padding-top: 9pt; border-top: 1px solid var(--line);
    font-family: "IBM Plex Mono", monospace; font-size: 8pt; letter-spacing: 0.05em;
    color: var(--ink-soft);
  }
  :root.lang-go .hero .lede::after {
    content: "This copy carries the Go snippets. For the Python half, switch with the control in the bar and print again.";
  }
  :root.lang-py .hero .lede::after {
    content: "This copy carries the Python snippets. For the Go half, switch with the control in the bar and print again.";
  }
`;

// The algorithms page is half interactive figures. On paper the controls mean
// nothing and are dropped, but what the figures *show* is the argument, so the
// fills stay: print-color-adjust tells Chrome to print them even with
// "Background graphics" off, which is the default. Everything here is a
// snapshot of the figure's opening frame, because nothing on that page
// autoplays -- so the printed copy is deterministic.
const DSA = `
  /* the controls, and the two lines that only make sense on screen */
  .demo-ctl, figure.demo .nojs { display: none !important; }
  figure.demo { break-inside: avoid; }
  .demo-stage { overflow: visible; padding: 10pt 12pt; }
  .demo-head { padding: 7pt 12pt; }
  .demo-read { padding: 6pt 12pt; font-size: 7.4pt; min-height: 0; }
  figure.demo figcaption { padding: 0 12pt 10pt; }
  .demo-legend { font-size: 6.6pt; margin-top: 8pt; }

  /* keep the fills: without them a bar chart is blank paper */
  .bars, .bars .bar, .cell, .grid, .grid b, .dp td, .dp th,
  .demo-stage svg, .demo-legend i, .langbar {
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }
  .bars { height: 110pt; }

  /* the pathfinding grid is 39 columns wide and the text block is not */
  .grid { --cs: 13px; }

  /* On screen a highlighted node or cell reverses white text out of a colour.
     On paper that is the one thing that cannot be checked for contrast, so the
     highlight becomes an outline and every character stays dark on white. */
  .dp td.now, .dp td.trace {
    background: none !important; color: var(--ink) !important; font-weight: 700;
    box-shadow: inset 0 0 0 2px var(--l2);
  }
  .dp td.trace { box-shadow: inset 0 0 0 2px var(--l1); }
  .demo-stage svg .node.on circle, .demo-stage svg .node.on rect,
  .demo-stage svg .node.ok circle, .demo-stage svg .node.ok rect,
  .demo-stage svg .node.hot circle, .demo-stage svg .node.hot rect { fill: none; stroke-width: 2.4; }
  .demo-stage svg .node.on text, .demo-stage svg .node.ok text,
  .demo-stage svg .node.hot text { fill: var(--ink); }

  /* auto-fit grids, pinned the way the rest of the print sheet pins them */
  .growth { grid-template-columns: 1fr 1fr; gap: 14pt; }
  .svc { grid-template-columns: repeat(2, 1fr); }

  /* which of the three languages this copy carries */
  .langnote { display: none; }
  .hero .lede::after {
    display: block; margin-top: 14pt; padding-top: 9pt; border-top: 1px solid var(--line);
    font-family: "IBM Plex Mono", monospace; font-size: 8pt; letter-spacing: 0.05em;
    color: var(--ink-soft);
  }
  :root.lang-go .hero .lede::after {
    content: "This copy carries the Go snippets. Switch with the control in the bar and print again for Python or Java.";
  }
  :root.lang-py .hero .lede::after {
    content: "This copy carries the Python snippets. Switch with the control in the bar and print again for Go or Java.";
  }
  :root.lang-java .hero .lede::after {
    content: "This copy carries the Java snippets. Switch with the control in the bar and print again for Go or Python.";
  }
  .hero .lede::before {
    display: block; margin-top: 14pt; padding-top: 9pt; border-top: 1px solid var(--line);
    font-family: "IBM Plex Mono", monospace; font-size: 8pt; letter-spacing: 0.05em;
    color: var(--ink-soft);
    content: "The figures below are interactive on screen; printed, each one shows its opening state.";
  }
`;

// The three passes all splice a block in ahead of the next marker, and each one
// leaves its own idea of the blank line before it. Left alone they leapfrog and
// the file grows a newline per full run. Normalising the gap here -- in all
// three passes, identically -- makes the composition converge.
const tidy = t => t.replace(/\n{2,}(?=<!-- \/?(?:highlight|print|glossary) -->)/g, '\n');

const base = fs.readFileSync('print.css', 'utf8').replace('/*TOKENS*/', tokens());

for (const page of PAGES) {
  let s = fs.readFileSync(page, 'utf8');

  // Per-page additions go inside the same @media print block, before its brace.
  const extra = page === 'aws-deep-dive.html' ? AWS : page === 'dsa.html' ? DSA : '';
  const sheet = base.replace(/\n\}\n$/, extra + '}').replace(/\n+$/, '');
  const css = [OPEN, '<style>', sheet, '</style>', CLOSE, ''].join('\n');

  if (s.includes(OPEN)) {
    const tail = s.indexOf(CLOSE) + CLOSE.length;
    s = s.slice(0, s.indexOf(OPEN)) + s.slice(s[tail] === '\n' ? tail + 1 : tail);
  }
  s = s.includes(GLOSS) ? s.replace(GLOSS, css + GLOSS) : s.replace(/\n*$/, '\n') + css;

  if (!CHECK) fs.writeFileSync(page, tidy(s));
  console.log(`${page.padEnd(26)} ${String(css.length).padStart(5)} bytes${extra ? '  + page rules' : ''}`);
}
