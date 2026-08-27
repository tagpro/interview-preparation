// Prove the site needs no network.
//
// Every request that is not a local file is aborted, so anything the pages
// still reach for shows up as a failure rather than as a silent fallback. Then
// the fonts are checked for real: not "the stylesheet linked", but "the browser
// has these faces and would use them".
//
//     node offline_check.mjs <site-root>
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const SITE = path.resolve(process.argv[2]);
const WANT = ['Bricolage Grotesque', 'IBM Plex Sans', 'IBM Plex Mono'];

function pages(dir, acc = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { if (e.name !== 'build') pages(p, acc); }
    else if (e.name.endsWith('.html')) acc.push(p);
  }
  return acc;
}

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let bad = 0;

for (const file of pages(SITE).sort()) {
  const page = await browser.newPage();
  const reachedOut = [];
  const failed = [];
  await page.route('**/*', route => {
    const url = route.request().url();
    if (url.startsWith('file://') || url.startsWith('data:') || url.startsWith('about:')) return route.continue();
    reachedOut.push(url);
    return route.abort();
  });
  page.on('requestfailed', r => { if (!reachedOut.includes(r.url())) failed.push(r.url()); });

  await page.goto('file://' + file, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(200);

  // check() implies weight 400 unless told otherwise, and Bricolage ships only
  // 500/700/800 -- so ask each family at a weight it actually has.
  const fonts = await page.evaluate(w => {
    const faces = [...document.fonts];
    const loaded = faces.filter(f => f.status === 'loaded');
    const name = f => f.family.replace(/['"]/g, '');
    return {
      status: document.fonts.status,
      loaded: loaded.map(name),
      usable: w.map(fam => {
        const weights = [...new Set(loaded.filter(f => name(f) === fam).map(f => f.weight))];
        return weights.length > 0 && weights.some(wt => document.fonts.check(`${wt} 16px "${fam}"`));
      }),
      weights: w.map(fam => [...new Set(loaded.filter(f => name(f) === fam).map(f => f.weight))].join('/')),
    };
  }, WANT);
  await page.close();

  const missing = WANT.filter((f, i) => !fonts.usable[i]);
  const issues = [];
  if (reachedOut.length) issues.push(`network: ${[...new Set(reachedOut)].slice(0, 3).join(', ')}`);
  if (failed.length) issues.push(`failed: ${failed.slice(0, 2).join(', ')}`);
  if (missing.length) issues.push(`font not usable offline: ${missing.join(', ')}`);
  if (issues.length) bad++;

  console.log(`${issues.length ? 'FAIL' : '  ok'}  ${path.relative(SITE, file).padEnd(30)} ` +
    `fonts ${fonts.status}, ${new Set(fonts.loaded).size} families ` +
    `(${WANT.map((f, i) => f.split(' ').pop() + ' ' + fonts.weights[i]).join(', ')})` +
    (issues.length ? `\n      ${issues.join('; ')}` : ''));
}
await browser.close();
console.log(`\n${bad === 0 ? 'FULLY OFFLINE' : bad + ' PAGE(S) STILL NEED THE NETWORK'}`);
process.exit(bad ? 1 : 0);
