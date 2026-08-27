// Every character the pages previously dimmed (<span class="c">) must still be
// dimmed now (th-comment or th-meta). Compares decoded character offsets, so it
// is immune to differences in how the markup is nested.
import fs from 'node:fs';
import { PAGES, detect } from './hl_detect.mjs';
const txt0raw = f => dec(f.replace(/<[^>]+>/g, ''));

const ENT = { lt: '<', gt: '>', amp: '&', quot: '"', apos: "'", '#39': "'",
              larr: '←', rarr: '→', rsquo: '’', mdash: '—', ndash: '–', nbsp: ' ' };
const dec = s => s.replace(/&(#39|#x27|lt|gt|amp|quot|apos|larr|rarr|rsquo|mdash|ndash|nbsp);/g,
  (_, k) => ENT[k === '#x27' ? '#39' : k]);

// Walk markup, tracking which decoded offsets sit inside a span matching `want`.
function covered(frag, want) {
  const set = new Set();
  let out = 0, depth = 0, inside = 0;
  const re = /<(\/?)span([^>]*)>|([^<]+)/g;
  let m;
  while ((m = re.exec(frag))) {
    if (m[3] !== undefined) { const t = dec(m[3]);
      for (let i = 0; i < t.length; i++) if (inside) set.add(out + i);
      out += t.length; continue; }
    if (m[1]) { depth--; if (inside && depth < inside) inside = 0; }
    else { depth++; if (!inside && want.test(m[2])) inside = depth; }
  }
  return set;
}

const RE = /<pre([^>]*)>([\s\S]*?)<\/pre>/g;
let lost = 0, blocks = 0, gained = 0;
for (const p of PAGES) {
  const ob = [...fs.readFileSync('_bak/' + p, 'utf8').matchAll(RE)];
  const nb = [...fs.readFileSync(p, 'utf8').matchAll(RE)];
  for (let i = 0; i < ob.length; i++) {
    const was = covered(ob[i][2], /class="c"/);
    const now = covered(nb[i][2], /th-(comment|meta)/);
    const txt0 = dec(ob[i][2].replace(/<[^>]+>/g, ''));
    // Whitespace-only differences are invisible: the old markup wrapped a whole
    // run of output in one span (newlines included), this emits one range per line.
    const missing = [...was].filter(x => !now.has(x) && /\S/.test(txt0[x] || ''));
    gained += [...now].filter(x => !was.has(x) && /\S/.test(txt0raw(ob[i][2])[x] || '')).length;
    if (missing.length) {
      lost += missing.length; blocks++;
      console.log(`${p.replace('.html','')} #${i+1} ${detect(ob[i][2], ob[i][1], p)}: ${missing.length} chars`);
      console.log(`   e.g. ${JSON.stringify(txt0.slice(missing[0], missing[0] + 90))}`);
    }
  }
}
console.log(`\n${lost ? blocks + ' blocks lost dimming (' + lost + ' chars)' : 'no dimmed text was lost'}; ${gained} chars newly dimmed`);
process.exit(lost ? 1 : 0);
