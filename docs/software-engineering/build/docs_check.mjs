// The two hand-maintained pages at the root of the Pages directory: does every
// link land on a file that exists, and do they render at all.
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const DOCS = path.resolve(process.argv[2]);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let bad = 0;

for (const file of ['index.html', '404.html']) {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e).split('\n')[0]));
  await page.goto('file://' + path.join(DOCS, file), { waitUntil: 'load' });

  const r = await page.evaluate(() => ({
    title: document.title,
    lang: document.documentElement.lang,
    desc: (document.querySelector('meta[name=description]') || {}).content || '',
    icon: !!document.querySelector('link[rel=icon]'),
    h1: (document.querySelector('h1') || {}).textContent || '',
    bg: getComputedStyle(document.body).backgroundColor,
    links: [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href')),
  }));
  await page.close();

  const issues = [];
  // site-root links resolve at serve time, not on disk
  for (const href of r.links.filter(h => !/^(https?:|#|\/$)/.test(h))) {
    if (!fs.existsSync(path.join(DOCS, href.replace(/\/$/, '/index.html')))) issues.push(`dead: ${href}`);
  }
  if (!r.title) issues.push('no title');
  if (r.lang !== 'en') issues.push('no lang');
  if (file === 'index.html' && !r.desc) issues.push('no description');
  if (!r.icon) issues.push('no favicon');
  if (r.bg === 'rgba(0, 0, 0, 0)') issues.push('transparent body background');
  if (errors.length) issues.push(`js: ${errors[0]}`);
  if (issues.length) bad++;

  console.log(`${issues.length ? 'FAIL' : '  ok'}  ${file.padEnd(12)} ` +
    `${r.links.length} links  bg ${r.bg}  "${r.h1.replace(/\s+/g, ' ').trim().slice(0, 40)}"` +
    (issues.length ? `\n      ${issues.join('; ')}` : ''));
}
await browser.close();
console.log(`\n${bad === 0 ? 'DOCS ROOT CLEAN' : bad + ' PAGE(S) WITH ISSUES'}`);
process.exit(bad ? 1 : 0);
