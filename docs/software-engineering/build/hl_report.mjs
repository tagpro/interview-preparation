import fs from 'node:fs';
import { PAGES, detect, strip, fingerprint } from './hl_detect.mjs';
const RE = /<pre([^>]*)>([\s\S]*?)<\/pre>/g;
const tally = {};
for (const p of PAGES) {
  const s = fs.readFileSync(p, 'utf8');
  let m, i = 0;
  while ((m = RE.exec(s))) {
    const lang = detect(m[2], m[1], p);
    tally[lang] = (tally[lang] || 0) + 1;
    const t = strip(m[2]);
    const l0 = t.split('\n').filter(x => x.trim())[0] || '';
    console.log(`${p.replace('.html','').padEnd(20)} #${String(++i).padStart(3)} ${lang.padEnd(10)} ${fingerprint(t)} | ${l0.trim().slice(0,60)}`);
  }
}
console.error('TALLY', JSON.stringify(tally));
