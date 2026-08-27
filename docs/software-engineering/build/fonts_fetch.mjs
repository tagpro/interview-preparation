// Cache the pages' Google fonts locally, for print_pdf.mjs.
//
// A file:// render usually cannot reach fonts.googleapis.com, and the fallback
// mono has different metrics -- which would put the wrapping of every code line
// in the wrong place and make the print checks measure the wrong document. This
// fetches the exact faces the pages ask for and rewrites the stylesheet to
// point at them. Output lands in _fonts/ and is not committed.
//
//     node fonts_fetch.mjs
import fs from 'node:fs';

const URL_ = 'https://fonts.googleapis.com/css2' +
  '?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800' +
  '&family=IBM+Plex+Sans:wght@400;500;600' +
  '&family=IBM+Plex+Mono:wght@400;500;600&display=swap';
// Google serves woff2 only to browsers that say they can take it.
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';

fs.mkdirSync('_fonts', { recursive: true });
let css = await (await fetch(URL_, { headers: { 'User-Agent': UA } })).text();

const urls = [...new Set([...css.matchAll(/url\((https:\/\/fonts\.gstatic\.com\/[^)]+)\)/g)].map(m => m[1]))];
let n = 0;
for (const url of urls) {
  const name = `f${String(++n).padStart(2, '0')}.woff2`;
  const buf = Buffer.from(await (await fetch(url)).arrayBuffer());
  fs.writeFileSync(`_fonts/${name}`, buf);
  css = css.split(url).join(`_fonts/${name}`);   // resolved against the page, not this file
  process.stdout.write(`\r${n}/${urls.length} faces`);
}
fs.writeFileSync('_fonts/local.css', css);
console.log(`\n_fonts/local.css written, ${urls.length} faces`);
