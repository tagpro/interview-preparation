// Check the web app manifest against a real server, not against path arithmetic.
//
// Serves the site over HTTP, loads it in a browser, and verifies the manifest
// the way a browser would: fetched from the page's own link, parsed, every icon
// and shortcut actually retrievable, and every PNG the size it claims to be.
//
//     node manifest_check.mjs <site-root>
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { chromium } from 'playwright';

const SITE = path.resolve(process.argv[2]);
const TYPES = { '.html': 'text/html', '.json': 'application/json', '.css': 'text/css',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };

const server = http.createServer((req, res) => {
  let p = path.join(SITE, decodeURIComponent(req.url.split('?')[0]));
  if (fs.existsSync(p) && fs.statSync(p).isDirectory()) p = path.join(p, 'index.html');
  if (!p.startsWith(SITE) || !fs.existsSync(p)) { res.writeHead(404); return res.end('not found'); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, r));
const base = `http://127.0.0.1:${server.address().port}`;

// PNG dimensions come out of the IHDR chunk, so the declared size is checked
// against the actual pixels rather than against the filename.
function pngSize(buf) {
  if (buf.slice(1, 4).toString() !== 'PNG') return null;
  return `${buf.readUInt32BE(16)}x${buf.readUInt32BE(20)}`;
}

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const page = await browser.newPage();
await page.goto(base + '/', { waitUntil: 'load' });

const href = await page.evaluate(() => {
  const l = document.querySelector('link[rel=manifest]');
  return l ? l.href : null;
});
const issues = [];
if (!href) issues.push('no <link rel=manifest> on the front page');

const res = await page.request.get(href);
const mime = res.headers()['content-type'] || '';
const m = await res.json();
console.log(`manifest      ${href.replace(base, '')}  ${res.status()}  ${mime}`);
console.log(`name          "${m.name}"  /  "${m.short_name}"`);
console.log(`display       ${m.display}   scope ${m.scope}   start_url ${m.start_url}`);
console.log(`colors        theme ${m.theme_color}  background ${m.background_color}`);

for (const f of ['name', 'short_name', 'start_url', 'display', 'icons'])
  if (!m[f]) issues.push(`missing required field: ${f}`);
if (!['standalone', 'fullscreen', 'minimal-ui'].includes(m.display))
  issues.push(`display "${m.display}" is not installable`);

// every icon must actually be retrievable, and be the size it says
console.log('\nicons');
for (const icon of m.icons || []) {
  const url = new URL(icon.src, href).href;
  const r = await page.request.get(url);
  let real = icon.sizes;
  if (icon.type === 'image/png') {
    real = pngSize(await r.body()) || '?';
    if (real !== icon.sizes) issues.push(`${icon.src}: declared ${icon.sizes}, actually ${real}`);
  }
  if (!r.ok()) issues.push(`${icon.src}: HTTP ${r.status()}`);
  console.log(`  ${r.ok() ? 'ok' : r.status()}  ${icon.src.padEnd(30)} ${String(icon.sizes).padEnd(9)} ` +
    `${(icon.purpose || 'any').padEnd(9)} ${real === icon.sizes ? '' : '-> real ' + real}`);
}
const purposes = new Set((m.icons || []).flatMap(i => (i.purpose || 'any').split(' ')));
const pngSizes = new Set((m.icons || []).filter(i => i.type === 'image/png').map(i => i.sizes));
for (const need of ['192x192', '512x512'])
  if (!pngSizes.has(need)) issues.push(`no ${need} PNG icon -- Chrome requires one`);
if (!purposes.has('maskable')) issues.push('no maskable icon -- Android will letterbox it');

// start_url and every shortcut must land on a real page
console.log('\nlinks');
for (const [label, url] of [['start_url', m.start_url],
    ...(m.shortcuts || []).map(s => [`shortcut: ${s.short_name}`, s.url])]) {
  const r = await page.request.get(new URL(url, href).href);
  if (!r.ok()) issues.push(`${label} -> ${url}: HTTP ${r.status()}`);
  console.log(`  ${r.ok() ? 'ok' : r.status()}  ${label.padEnd(28)} ${url}`);
}

// apple-touch-icon, which iOS uses instead of the manifest's icons
const apple = await page.evaluate(() => {
  const l = document.querySelector('link[rel="apple-touch-icon"]');
  return l ? l.href : null;
});
if (!apple) issues.push('no apple-touch-icon -- iOS home screen would use a screenshot');
else {
  const r = await page.request.get(apple);
  const real = pngSize(await r.body());
  console.log(`  ${r.ok() ? 'ok' : r.status()}  ${'apple-touch-icon'.padEnd(28)} ${real}`);
  if (!r.ok()) issues.push(`apple-touch-icon: HTTP ${r.status()}`);
}

const sw = await page.evaluate(() => navigator.serviceWorker.controller !== null ||
  navigator.serviceWorker.getRegistrations().then(r => r.length > 0));
await browser.close();
server.close();

console.log('\n' + (issues.length ? issues.map(i => 'FAIL  ' + i).join('\n') : 'MANIFEST OK'));
console.log(sw ? 'service worker: registered' :
  'service worker: none -- Chrome will not offer to install without one');
process.exit(issues.length ? 1 : 0);
