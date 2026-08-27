// The app icon, drawn rather than borrowed.
//
// The site's favicons are emoji in a data URI, which is fine for a browser tab
// and no good as an installed icon: emoji render differently on every platform
// and not at all where no colour emoji font is installed. This draws the mark in
// plain SVG shapes -- no font, no external asset -- and renders it at the sizes
// a manifest and iOS actually want.
//
//     node icons_build.mjs <out-dir>
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const OUT = path.resolve(process.argv[2] || 'icons');

// The series' own dark palette: the three rungs are its three levels, bottom to
// top, which is what the ladder in "The Backend Ladder" refers to.
const INK = '#0B1218', RAIL = '#E2EAEF';
const L1 = '#3EC0CC', L2 = '#8E9BEC', L3 = '#E7935B';

// `inset` is how far the mark sits from the edge: small for an icon shown as
// drawn, large for a maskable one, where a platform may crop to a circle and
// only the middle 80% is guaranteed to survive.
function mark({ plateRadius, inset }) {
  const s = 512, m = inset, span = s - 2 * m;
  const railW = span * 0.10, rungH = span * 0.095;
  const lx = m + span * 0.16, rx = m + span * 0.74;
  const rungs = [0.74, 0.45, 0.16].map((t, i) => ({
    y: m + span * t, fill: [L1, L2, L3][i],
  }));
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 ${s} ${s}">
  <rect width="${s}" height="${s}" rx="${plateRadius}" fill="${INK}"/>
  ${rungs.map(r => `<rect x="${lx}" y="${r.y}" width="${rx - lx + railW}" height="${rungH}" rx="${rungH / 2}" fill="${r.fill}"/>`).join('\n  ')}
  <rect x="${lx}" y="${m}" width="${railW}" height="${span}" rx="${railW / 2}" fill="${RAIL}"/>
  <rect x="${rx}" y="${m}" width="${railW}" height="${span}" rx="${railW / 2}" fill="${RAIL}"/>
</svg>`;
}

const ANY = mark({ plateRadius: 96, inset: 96 });        // shown as drawn
const MASKABLE = mark({ plateRadius: 0, inset: 128 });   // may be cropped to a circle

const TARGETS = [
  { file: 'icon-192.png', size: 192, svg: ANY },
  { file: 'icon-512.png', size: 512, svg: ANY },
  { file: 'icon-maskable-512.png', size: 512, svg: MASKABLE },
  // iOS ignores manifest icons for the home screen and rounds this itself,
  // so it must be square and full-bleed.
  { file: 'apple-touch-icon.png', size: 180, svg: MASKABLE },
];

fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(path.join(OUT, 'icon.svg'), ANY + '\n');

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
for (const t of TARGETS) {
  const page = await browser.newPage({ viewport: { width: t.size, height: t.size } });
  await page.setContent(
    `<style>html,body{margin:0;padding:0}svg{display:block;width:${t.size}px;height:${t.size}px}</style>` + t.svg);
  await page.screenshot({ path: path.join(OUT, t.file), omitBackground: true });
  await page.close();
  console.log(`${t.file.padEnd(24)} ${t.size}x${t.size}  ${(fs.statSync(path.join(OUT, t.file)).size / 1024).toFixed(1)} KB`);
}
await browser.close();
console.log(`icon.svg                 vector    ${(Buffer.byteLength(ANY) / 1024).toFixed(1)} KB`);
