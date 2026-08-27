// What actually lands on the page.
//
// Chrome's PDF/print backend does not always write the colour the stylesheet
// asked for: a handful of values come out noticeably darker. That is invisible
// on screen and only shows up in the printed copy, so every print token is
// rendered through the real pipeline here and compared with what was asked.
//
//     node print_ink.mjs                     # check the print palette
//     node print_ink.mjs '#6F42AF' '#5A42AF' # check specific candidates
import fs from 'node:fs';
import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import { printTheme, seriesTokens } from './print_theme.mjs';

const args = process.argv.slice(2).filter(a => a.startsWith('#'));
// Only colours that end up as text. Chrome deliberately darkens light *text*
// so it survives on paper -- pure white would land as grey -- so feeding it
// surface and border values would report shifts that never happen to them.
const INK = ['ink', 'ink-soft', 'ink-faint', 'l1', 'l2', 'l3', 'accent'];
const wanted = args.length
  ? args.map((c, i) => [`arg${i}`, c.toUpperCase()])
  : [...Object.entries(printTheme.tokens),
     ...INK.map(k => [k, seriesTokens[k]])]
    .map(([k, v]) => [k, v.toUpperCase()]);

const html = '<style>body{font:11pt monospace;margin:12px}div{margin:0}</style>' +
  wanted.map(([k, c]) => `<div style="color:${c}">${k} ${c}</div>`).join('');
fs.writeFileSync('/tmp/_ink.html', html);

const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const p = await b.newPage();
await p.goto('file:///tmp/_ink.html');
fs.writeFileSync('/tmp/_ink.pdf', await p.pdf({ format: 'A4', printBackground: false }));
await b.close();

const got = JSON.parse(execFileSync('python3', ['-c', `
import pymupdf, json
d = pymupdf.open('/tmp/_ink.pdf'); out = {}
for pg in d:
    for b in pg.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                t = s['text'].strip()
                if t: out[t.split()[0]] = '#%06X' % s['color']
print(json.dumps(out))`]).toString());

let bad = 0;
for (const [k, c] of wanted) {
  const landed = got[k] || '??';
  const ok = landed === c;
  if (!ok) bad++;
  console.log(`${ok ? '  ok' : 'SHIFT'}  ${k.padEnd(12)} asked ${c}   landed ${landed}`);
}
console.log(`\n${bad === 0 ? 'ALL FAITHFUL' : bad + ' COLOUR(S) SHIFTED IN THE PRINT PIPELINE'}`);
process.exit(bad ? 1 : 0);
