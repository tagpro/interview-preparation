// Prove the offline cache works, and that it updates.
//
// The network is taken away by SHUTTING THE SERVER DOWN, not by asking the
// browser to pretend. Playwright's offline emulation does not reliably reach a
// service worker's own fetches -- with it, pages that were quietly still being
// served over the network looked like cache hits. With the server stopped there
// is nothing to serve them but the cache.
//
// Runs against a copy, over HTTP on 127.0.0.1, which counts as a secure context.
//
//     node sw_check.mjs <site-root>
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import http from 'node:http';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright';

const SRC = path.resolve(process.argv[2]);
const SITE = fs.mkdtempSync(path.join(os.tmpdir(), 'swcheck-'));
fs.cpSync(SRC, SITE, { recursive: true });

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
  '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };

let server, sockets = new Set(), port = 0;
function start() {
  server = http.createServer((req, res) => {
    let p = path.join(SITE, decodeURIComponent(req.url.split('?')[0]));
    if (fs.existsSync(p) && fs.statSync(p).isDirectory()) p = path.join(p, 'index.html');
    if (!p.startsWith(SITE) || !fs.existsSync(p)) { res.writeHead(404); return res.end('not found'); }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream',
      'Cache-Control': 'no-cache' });
    fs.createReadStream(p).pipe(res);
  });
  server.on('connection', s => { sockets.add(s); s.on('close', () => sockets.delete(s)); });
  return new Promise(r => server.listen(port, '127.0.0.1', () => { port = server.address().port; r(); }));
}
// close() alone only stops new connections; keep-alive sockets would still serve.
function stop() {
  return new Promise(r => { for (const s of sockets) s.destroy(); sockets.clear(); server.close(r); });
}

await start();
const base = () => `http://127.0.0.1:${port}`;
const pages = ['/', '/404.html', ...fs.readdirSync(path.join(SITE, 'software-engineering'))
  .filter(f => f.endsWith('.html')).sort().map(f => '/software-engineering/' + f)];

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const context = await browser.newContext();
const page = await context.newPage();
const issues = [];

// --- install ----------------------------------------------------------------
await page.goto(base() + '/', { waitUntil: 'load' });
const installed = await page.evaluate(async () => {
  const reg = await navigator.serviceWorker.ready;
  for (let i = 0; i < 100 && !navigator.serviceWorker.controller; i++)
    await new Promise(r => setTimeout(r, 100));
  const names = await caches.keys();
  return { scope: reg.scope, controller: !!navigator.serviceWorker.controller, names,
           entries: (await (await caches.open(names[0])).keys()).length };
});
console.log(`installed     ${installed.names.join(', ')}, ${installed.entries} entries`);
console.log(`scope         ${installed.scope}`);
if (!installed.controller) issues.push('the worker never took control of the page');
if (installed.entries < 20) issues.push(`only ${installed.entries} entries precached`);

// --- the server goes away ----------------------------------------------------
await stop();
console.log(`\nserver stopped on port ${port} — anything that loads now came from the cache`);

for (const url of pages) {
  let ok = false, detail = '';
  try {
    const res = await page.goto(base() + url, { waitUntil: 'load' });
    const r = await page.evaluate(() => {
      const loaded = [...document.fonts].filter(f => f.status === 'loaded');
      const fam = f => f.family.replace(/['"]/g, '');
      // ask each family at a weight this page actually uses
      const usable = ['Bricolage Grotesque', 'IBM Plex Sans', 'IBM Plex Mono'].every(n => {
        const w = loaded.filter(f => fam(f) === n).map(f => f.weight);
        return w.length && w.some(x => document.fonts.check(`${x} 16px "${n}"`));
      });
      return { title: document.title, body: document.body.textContent.trim().length, usable };
    });
    ok = res.status() === 200 && r.body > 400 && r.usable;
    detail = `${r.title.slice(0, 24).padEnd(24)} ${String(r.body).padStart(6)} chars  fonts ${r.usable ? 'ok' : 'MISSING'}`;
  } catch (e) { detail = String(e).split('\n')[0].slice(0, 64); }
  if (!ok) issues.push(`offline: ${url} -- ${detail}`);
  console.log(`  ${ok ? 'ok' : 'FAIL'}  ${url.padEnd(38)} ${detail}`);
}

// a URL that was never cached still gets the site's own 404, not a browser error
try {
  await page.goto(base() + '/no/such/page.html', { waitUntil: 'load' });
  const title = await page.title();
  const served = title === 'Not found';
  if (!served) issues.push(`offline: an unknown URL gave "${title}", not the 404 page`);
  console.log(`  ${served ? 'ok' : 'FAIL'}  ${'/no/such/page.html'.padEnd(38)} -> "${title}"`);
} catch (e) { issues.push('offline: unknown URL threw ' + String(e).split('\n')[0].slice(0, 60)); }

// --- and it updates ----------------------------------------------------------
await start();
fs.appendFileSync(path.join(SITE, 'index.html'), '\n<!-- changed -->\n');
execFileSync('node', ['sw_build.mjs', SITE], { stdio: 'pipe' });
const after = await page.evaluate(async first => {
  const reg = await navigator.serviceWorker.getRegistration();
  await reg.update();
  for (let i = 0; i < 100; i++) {
    const names = (await caches.keys()).filter(n => n.startsWith('ladder-'));
    if (names.length === 1 && names[0] !== first) return names;
    await new Promise(r => setTimeout(r, 100));
  }
  return (await caches.keys()).filter(n => n.startsWith('ladder-'));
}, installed.names[0]);
const rolled = after.length === 1 && after[0] !== installed.names[0];
if (!rolled) issues.push(`after a content change the caches are [${after}], expected one new one`);
console.log(`\nchange a file  ${installed.names[0]} -> ${after.join(', ')}` +
  `${rolled ? '  (old cache deleted)' : ''}`);

await browser.close();
await stop();
fs.rmSync(SITE, { recursive: true, force: true });
console.log('\n' + (issues.length ? issues.map(i => 'FAIL  ' + i).join('\n') : 'OFFLINE CACHE WORKS'));
process.exit(issues.length ? 1 : 0);
