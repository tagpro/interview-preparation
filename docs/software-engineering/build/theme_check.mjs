// Does the switch actually change the page, survive a reload, and stay out of
// the way inside an artifact?
//
//     node theme_check.mjs ../..        # the built site
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.argv[2] ?? '../..');
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
                '.woff2': 'font/woff2', '.json': 'application/json' };

const server = http.createServer((req, res) => {
  let p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (p.endsWith('/')) p += 'index.html';
  fs.readFile(p, (err, body) => {
    if (err) { res.writeHead(404); res.end('nope'); return; }
    res.writeHead(200, { 'content-type': TYPES[path.extname(p)] ?? 'application/octet-stream' });
    res.end(body);
  });
});
await new Promise(r => server.listen(0, r));
const base = `http://127.0.0.1:${server.address().port}`;

const PAGES = ['/software-engineering/', '/software-engineering/ai-engineering.html',
               '/software-engineering/algorithms.html', '/software-engineering/foundations.html',
               '/software-engineering/go.html', '/software-engineering/cloud.html',
               '/software-engineering/python.html', '/software-engineering/java.html',
               '/software-engineering/aws.html', '/', '/404.html'];

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let bad = 0;

for (const url of PAGES) {
  // A dark OS, so "system" and "light" must differ and the override must win.
  const ctx = await browser.newContext({ colorScheme: 'dark' });
  const page = await ctx.newPage();
  await page.goto(base + url, { waitUntil: 'load' });

  const bg = () => page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  const present = await page.$$eval('.themebar button', b => b.length);
  const systemBg = await bg();

  await page.click('.themebar button[data-theme-set="light"]');
  const lightBg = await bg();
  await page.click('.themebar button[data-theme-set="dark"]');
  const darkBg = await bg();

  // The choice has to outlive a navigation, or it is a gimmick.
  await page.click('.themebar button[data-theme-set="light"]');
  await page.reload({ waitUntil: 'load' });
  const afterReload = await bg();
  const pressed = await page.$eval('.themebar button[aria-pressed="true"]',
                                   b => b.getAttribute('data-theme-set'));
  // No flash: the attribute must be set before the body is painted, which means
  // it is already there when the very first script of the document runs.
  const early = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));

  await page.click('.themebar button[data-theme-set="system"]');
  const backToSystem = await bg();
  const cleared = await page.evaluate(() => document.documentElement.hasAttribute('data-theme'));

  const ok = present === 3 && systemBg === darkBg && lightBg !== darkBg &&
             afterReload === lightBg && pressed === 'light' && early === 'light' &&
             backToSystem === darkBg && !cleared;
  if (!ok) bad++;
  console.log(`  ${ok ? 'ok ' : 'FAIL'} ${url.padEnd(42)} buttons ${present}  ` +
              `system ${systemBg === darkBg ? 'dark' : '?'}  light!=dark ${lightBg !== darkBg}  ` +
              `survives reload ${afterReload === lightBg}  clears ${!cleared}`);
  await ctx.close();
}

// Framed, the artifact host owns the attribute: the control must stand down.
{
  const ctx = await browser.newContext({ colorScheme: 'dark' });
  const page = await ctx.newPage();
  await page.setContent(`<iframe src="${base}/software-engineering/ai-engineering.html"
                          style="width:900px;height:600px;border:0"></iframe>`);
  const frame = page.frameLocator('iframe');
  await page.waitForTimeout(900);
  const n = await frame.locator('.themebar').count();
  const attr = await frame.locator(':root').getAttribute('data-theme');
  const ok = n === 0 && attr === null;
  if (!ok) bad++;
  console.log(`  ${ok ? 'ok ' : 'FAIL'} framed: control hidden ${n === 0}, attribute untouched ${attr === null}`);
  await ctx.close();
}

await browser.close();
server.close();
console.log(bad ? `\n${bad} FAILURE(S)` : '\nTHEME SWITCH WORKS');
process.exit(bad ? 1 : 0);
