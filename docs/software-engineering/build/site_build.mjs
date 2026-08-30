// Build the static site from the eight built pages.
//
// The pages are written as artifact *fragments*: no <!doctype>, no <html>, no
// <head> -- the artifact host supplies those and puts the whole file in <body>.
// A real website has to provide them itself, and the series' cross-links point
// at claude.ai artifact URLs that mean nothing inside the site. This pass does
// both, and writes nothing back to the sources.
//
// `.nojekyll` is not written here -- it belongs at the root of the Pages
// publishing source, which is a level above this directory, and is committed
// once rather than regenerated.
//
//     node site_build.mjs <outdir> [site-root, relative to a page]
import fs from 'node:fs';
import path from 'node:path';

const OUT = process.argv[2];
if (!OUT) { console.error('usage: node site_build.mjs <outdir> [site-root]'); process.exit(2); }

// Where the site's shared files sit, relative to a page. These pages live one
// directory down; everything is relative rather than rooted at / because the
// site must also work opened straight off disk.
const ROOT = (process.argv[3] || '..').replace(/\/$/, '');

// The hub is the front door of the series, so it becomes the directory index.
const PAGES = [
  { src: 'backend-go-ladder.html',    out: 'index.html',      icon: '🪜',
    uuid: '7b938187-b51e-46cf-8191-2f7bca007bd3' },
  { src: 'pillar-a-foundations.html', out: 'foundations.html', icon: '⚙️',
    uuid: '25b57aa1-de16-48d9-bc41-fbd5857dd97f' },
  { src: 'pillar-b-go.html',          out: 'go.html',          icon: '🐹',
    uuid: '513b3fa1-6b65-4c47-84da-25734edb3c3f' },
  { src: 'pillar-c-cloud.html',       out: 'cloud.html',       icon: '☁️',
    uuid: '3e17f5fe-161e-41bd-90a9-baca241492b5' },
  { src: 'python-foundations.html',   out: 'python.html',      icon: '🐍',
    uuid: '9a2c6334-1c38-40c7-a916-c2fa95d490c4' },
  { src: 'java-spring.html',          out: 'java.html',        icon: '☕',
    uuid: '5695328e-c427-4d93-b1d2-b7a3d48f675b' },
  { src: 'aws-deep-dive.html',        out: 'aws.html',         icon: '🧰' ,
    uuid: 'd8c052d4-750f-4967-bb0f-7d6a048681e6' },
  { src: 'dsa.html',                  out: 'algorithms.html',  icon: '🧮',
    uuid: 'de1c07a0-10a5-42a5-ac59-582c4a48cc19' },
  { src: 'ai.html',                   out: 'ai-engineering.html', icon: '🧠',
    uuid: '934e618a-db2e-4b3d-8cd1-0d3a58ac2a5c' },
];
const BY_UUID = Object.fromEntries(PAGES.map(p => [p.uuid, p.out]));

const ENT = { lt: '<', gt: '>', amp: '&', quot: '"', apos: "'", '#39': "'", nbsp: ' ',
              mdash: '—', ndash: '–', rsquo: '’', lsquo: '‘', ldquo: '“', rdquo: '”',
              middot: '·', larr: '←', rarr: '→', hellip: '…' };
const decode = s => s.replace(/&(#39|#x27|lt|gt|amp|quot|apos|nbsp|mdash|ndash|rsquo|lsquo|ldquo|rdquo|middot|larr|rarr|hellip);/g,
  (_, k) => ENT[k === '#x27' ? '#39' : k] ?? _);
const attr = s => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// Registers the offline cache. Fails quietly where it cannot run -- opened off
// disk, or in a browser without service workers -- because the site works
// without it either way.
// The colour-theme switch, written by theme_sync.py from theme_ui.py. Read
// rather than inlined so there is one source for it; missing means the sync
// pass has not run, and shipping a site with no switch quietly is worse than
// stopping here.
const THEME = (() => {
  try {
    return fs.readFileSync('theme_block.html', 'utf8').replace(/\n*$/, '');
  } catch {
    console.error('theme_block.html is missing -- run: python3 theme_sync.py');
    process.exit(1);
  }
})();

const register = src => `<script>
if ("serviceWorker" in navigator) {
  addEventListener("load", function () {
    navigator.serviceWorker.register("${src}").catch(function () {});
  });
}
</script>`;

// An emoji favicon, the same one the artifact carries, as a self-contained SVG.
const favicon = emoji =>
  'data:image/svg+xml,' + encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">` +
    `<text x="6" y="78" font-size="76">${emoji}</text></svg>`);

// The search snippet, in the page's own words: whole sentences off the top of
// the hero lede while they fit, and a clean truncation when the first sentence
// is short and the second is a paragraph.
function description(body) {
  const m = body.match(/<p class="lede">([\s\S]*?)<\/p>/);
  if (!m) return '';
  const text = decode(m[1].replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
  let out = '';
  for (const part of text.split(/(?<=[.?!])\s+/)) {
    if (out && (out + ' ' + part).length > 155) break;
    out = out ? out + ' ' + part : part;
    if (out.length > 100) break;
  }
  if (out.length >= 80 && out.length <= 160) return out;
  const cut = text.slice(0, 152);
  return cut.slice(0, cut.lastIndexOf(' ')).replace(/[,;:—-]$/, '') + '…';
}

fs.mkdirSync(OUT, { recursive: true });
let leftovers = 0;

for (const page of PAGES) {
  const raw = fs.readFileSync(page.src, 'utf8');
  const lines = raw.split('\n');

  // The fragment opens with <title> and the three font links; those belong in
  // <head>. Everything after them -- styles, content, scripts -- stays put, in
  // the same order the artifact host renders it in.
  const title = lines[0].match(/^<title>(.*)<\/title>$/);
  const links = lines.slice(1, 4);
  if (!title || !links.every(l => l.startsWith('<link '))) {
    console.error(`${page.src}: unexpected prologue`); process.exit(1);
  }
  if (!links.some(l => l.includes('fonts.googleapis.com/css2'))) {
    console.error(`${page.src}: expected a Google Fonts stylesheet to replace`); process.exit(1);
  }
  let body = lines.slice(4).join('\n').replace(/^\n+/, '');

  // Series cross-links point at artifact URLs. Inside the site they are
  // ordinary relative links, and should not open a new tab.
  body = body.replace(/<a\b[^>]*>/g, tag => {
    const m = tag.match(/href="https:\/\/claude\.ai\/code\/artifact\/([0-9a-f-]+)"/);
    if (!m || !BY_UUID[m[1]]) return tag;
    return tag.replace(m[0], `href="${BY_UUID[m[1]]}"`)
              .replace(/\s+target="_blank"/g, '').replace(/\s+rel="noopener"/g, '');
  });
  const stray = body.match(/https:\/\/claude\.ai\/code\/artifact\/[0-9a-f-]+/g);
  if (stray) { leftovers += stray.length; console.error(`  ${page.src}: ${stray.length} artifact URL(s) left`); }

  const html = [
    '<!doctype html>',
    '<html lang="en">',
    '<head>',
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    '<meta name="color-scheme" content="light dark">',
    `<title>${title[1]}</title>`,
    `<meta name="description" content="${attr(description(body))}">`,
    // The browser UI follows the page, which follows the system.
    '<meta name="theme-color" content="#F2F5F7" media="(prefers-color-scheme: light)">',
    '<meta name="theme-color" content="#0B1218" media="(prefers-color-scheme: dark)">',
    `<link rel="icon" href="${favicon(page.icon)}">`,
    // The artifacts load their fonts from Google -- the only host their CSP
    // allows, and they have nowhere to put a file. The site serves its own.
    `<link rel="stylesheet" href="${ROOT}/fonts/fonts.css">`,
    '</head>',
    '<body>',
    // A site feature, not a page feature: the artifacts get a theme control
    // from the claude.ai host, which stamps the same data-theme attribute, and
    // two writers for one attribute is a fight. Generated by theme_sync.py.
    THEME,
    body.replace(/\n*$/, ''),
    register(`${ROOT}/sw.js`),
    '</body>',
    '</html>',
    '',
  ].join('\n');

  fs.writeFileSync(path.join(OUT, page.out), html);
  console.log(`${page.src.padEnd(26)} -> ${page.out.padEnd(18)} ${(html.length / 1024).toFixed(0).padStart(4)} KB  ${title[1]}`);
}

console.log('\n' + (leftovers ? `${leftovers} UNRESOLVED ARTIFACT URL(S)` : 'all cross-links resolved'));
process.exit(leftovers ? 1 : 0);
