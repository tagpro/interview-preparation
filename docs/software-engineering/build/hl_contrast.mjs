import { lightTheme, darkTheme } from './hl_theme.mjs';
import { printTheme } from './print_theme.mjs';
const lin = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
const L = hex => { const [r,g,b] = [1,3,5].map(i => parseInt(hex.slice(i, i+2), 16));
  return 0.2126*lin(r) + 0.7152*lin(g) + 0.0722*lin(b); };
const ratio = (a,b) => { const [x,y] = [L(a), L(b)].sort((p,q) => q-p); return (x+0.05)/(y+0.05); };
let bad = 0;
for (const t of [lightTheme, darkTheme, printTheme]) {
  console.log(`\n--- ${t.name} (bg ${t.background})`);
  for (const [k, v] of Object.entries(t.tokens)) {
    const r = ratio(v, t.background);
    // Body text wants 4.5:1; comments are deliberately quiet, so 3.5:1 there.
    // Comments are deliberately quiet, so 3.5:1 there -- except on paper, where
    // ink reads lighter than the same value backlit and they are pulled up.
    const quiet = k === 'comment' || k === 'meta';
    const min = quiet ? (t.type === 'print' ? 4.5 : 3.5) : 4.5;
    const ok = r >= min;
    if (!ok) bad++;
    console.log(`${ok ? '  ok' : 'FAIL'}  ${k.padEnd(12)} ${v}  ${r.toFixed(2)}:1  (min ${min})`);
  }
}
console.log(`\n${bad === 0 ? 'ALL PASS' : bad + ' FAILURES'}`);
process.exit(bad ? 1 : 0);
