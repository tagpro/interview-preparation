// Render every page the way a browser's Print command would, so the print
// stylesheet can be checked against real paper rather than guessed at.
//
// printBackground defaults to false to match Chrome's print dialog, where
// "Background graphics" starts unticked -- the harder of the two cases.
//
//     node print_pdf.mjs            # A4, backgrounds off
//     node print_pdf.mjs --bg       # backgrounds on
//     node print_pdf.mjs --letter
//     node print_pdf.mjs --dark     # printed from a dark-themed browser
//     node print_pdf.mjs path/to/fonts.css
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { PAGES } from './hl_detect.mjs';

const bg = process.argv.includes('--bg');
const dark = process.argv.includes('--dark');
const format = process.argv.includes('--letter') ? 'Letter' : 'A4';
const dir = `pdf${format === 'Letter' ? '-letter' : ''}${bg ? '-bg' : ''}${dark ? '-dark' : ''}`;
fs.mkdirSync(dir, { recursive: true });

// The site's own self-hosted faces -- the same ones it ships -- rather than a
// separate cache. Resolved from this script rather than the working directory,
// and overridable by passing a path, so it works from anywhere.
const here = path.dirname(fileURLToPath(import.meta.url));
const FONTS = path.resolve(process.argv.slice(2).find(a => a.endsWith('.css'))
  || path.join(here, '../../fonts/fonts.css'));
if (!fs.existsSync(FONTS)) console.error(`  (no ${FONTS} -- wrapping will measure the fallback font)`);

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const page = await browser.newPage();

for (const f of PAGES) {
  await page.goto('file://' + process.cwd() + '/' + f, { waitUntil: 'load' });
  await page.waitForFunction(() => document.querySelector('abbr.gl') !== null, null, { timeout: 5000 })
    .catch(() => console.error(`  (no abbr wrapped on ${f})`));
  // These pages are artifact sources and still link Google Fonts, which a
  // file:// render cannot reach. Serve the same faces from disk instead --
  // metrics decide where code lines wrap, and a fallback mono would measure a
  // different document.
  if (fs.existsSync(FONTS)) await page.addStyleTag({ url: 'file://' + FONTS });
  if (dark) await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'dark'));
  await page.evaluate(() => document.fonts.ready);
  const out = `${dir}/${f.replace('.html', '.pdf')}`;
  await page.pdf({ path: out, format, printBackground: bg, preferCSSPageSize: false });
  const fonts = await page.evaluate(() =>
    [...document.fonts].filter(x => x.status === 'loaded').map(x => x.family).filter((v, i, a) => a.indexOf(v) === i));
  console.log(`${f.padEnd(26)} ${(fs.statSync(out).size / 1024).toFixed(0).padStart(5)} KB   fonts: ${fonts.join(', ') || 'none loaded (fallbacks)'}`);
}
await browser.close();
