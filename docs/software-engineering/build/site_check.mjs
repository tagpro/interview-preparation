// Load every built page as a real document and check the things wrapping a
// fragment can break: parse errors, a missing stylesheet, dead cross-links, the
// runtime passes (contents rail, glossary, language switch) not running.
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const DIR = path.resolve(process.argv[2]);
const files = fs.readdirSync(DIR).filter(f => f.endsWith('.html')).sort();
// A handful of HTML tag names force the parser out of SVG foreign content, so
// one <b> inside a <text> ends the <svg> there and dumps the rest of the figure
// into the page as body text. It still parses, still passes a geometry audit of
// what is left, and looks catastrophic. Source-level, because by the time the
// DOM exists the evidence is a pile of stray nodes rather than a tag.
const BREAKOUT = /<(b|big|blockquote|body|br|center|code|dd|div|dl|dt|em|embed|h[1-6]|head|hr|i|img|li|listing|menu|meta|nobr|ol|p|pre|ruby|s|small|span|strong|strike|sub|sup|table|tt|u|ul|var)\b[^>]*>/;
let broken = 0;
for (const f of files) {
  const src = fs.readFileSync(path.join(DIR, f), 'utf8');
  for (const svg of src.match(/<svg\b[\s\S]*?<\/svg>/g) || []) {
    const m = BREAKOUT.exec(svg);
    if (!m) continue;
    broken++;
    const at = svg.slice(Math.max(0, m.index - 50), m.index + 30).replace(/\s+/g, ' ');
    console.log(`FAIL  ${f.padEnd(18)} <${m[1]}> inside <svg> breaks the figure: ...${at}...`);
  }
}

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let bad = broken;

for (const f of files) {
  const page = await browser.newPage();
  // Google Fonts is unreachable from a file:// page in this sandbox, and the
  // resulting resource error says nothing about the page. Everything else does.
  const NETWORK = /Failed to load resource|net::ERR_/;
  const errors = [];
  const fontFails = [];
  page.on('pageerror', e => errors.push(String(e).split('\n')[0]));
  page.on('console', m => {
    if (m.type() !== 'error') return;
    (NETWORK.test(m.text()) ? fontFails : errors).push(m.text().slice(0, 120));
  });
  await page.goto('file://' + path.join(DIR, f), { waitUntil: 'load' });
  await page.waitForTimeout(400);

  const r = await page.evaluate(() => {
    const links = [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href'));
    return {
      doctype: document.doctype ? document.doctype.name : null,
      title: document.title,
      lang: document.documentElement.lang,
      desc: (document.querySelector('meta[name=description]') || {}).content || '',
      icon: !!document.querySelector('link[rel=icon]'),
      home: [...document.querySelectorAll('a.homelink')].map(a => a.getAttribute('href')),
      styles: document.styleSheets.length,
      bodyBg: getComputedStyle(document.body).backgroundColor,
      // the three runtime passes
      tocLinks: document.querySelectorAll('.toc ol a').length,
      tocActive: document.querySelectorAll('.toc ol a.active').length,
      abbrs: document.querySelectorAll('abbr.gl').length,
      langClass: document.documentElement.className,
      hl: document.querySelectorAll('pre .th-token').length,
      pres: document.querySelectorAll('pre').length,
      // internal links, for the dead-link check
      local: links.filter(h => /^[\w.-]+\.html$/.test(h)),
      external: links.filter(h => /^https?:/.test(h)).length,
      inpage: links.filter(h => h.startsWith('#')).length,
      brokenAnchors: links.filter(h => h.startsWith('#') && !document.querySelector(h)).length,
    };
  });
  await page.close();

  const missing = [...new Set(r.local)].filter(h => !files.includes(h));
  const issues = [];
  if (r.doctype !== 'html') issues.push('no doctype');
  if (!r.title) issues.push('no title');
  if (r.lang !== 'en') issues.push('no lang');
  if (!r.desc) issues.push('no description');
  if (!r.icon) issues.push('no favicon');
  // The way back to the site's front page. Spliced in by site_build.mjs, so it
  // is exactly the kind of thing that can go missing without anything failing.
  if (r.home.length !== 1) issues.push(`${r.home.length} home link(s), expected 1`);
  else if (!fs.existsSync(path.resolve(DIR, r.home[0]))) issues.push(`home link goes nowhere: ${r.home[0]}`);
  if (r.styles < 2) issues.push(`only ${r.styles} stylesheet(s)`);
  if (r.tocLinks === 0) issues.push('contents rail empty');
  if (r.abbrs === 0) issues.push('glossary did not run');
  if (r.pres && r.hl === 0) issues.push('highlighting missing');
  if (missing.length) issues.push(`dead links: ${missing.join(', ')}`);
  if (r.brokenAnchors) issues.push(`${r.brokenAnchors} broken in-page anchor(s)`);
  if (r.external) issues.push(`${r.external} external link(s)`);
  if (errors.length) issues.push(`js: ${errors[0]}`);
  if (issues.length) bad++;

  console.log(`${issues.length ? 'FAIL' : '  ok'}  ${f.padEnd(18)} ` +
    `toc ${String(r.tocLinks).padStart(2)}  abbr ${String(r.abbrs).padStart(3)}  ` +
    `pre ${String(r.pres).padStart(2)}  spans ${String(r.hl).padStart(4)}  ` +
    `anchors ${String(r.inpage).padStart(2)}  ${(r.langClass || '-').padEnd(8)}` +
    `${fontFails.length ? ' (fonts offline)' : ''}` +
    (issues.length ? `\n      ${issues.join('; ')}` : ''));
}
await browser.close();
console.log(`\n${bad === 0 ? 'SITE CLEAN' : bad + ' PAGE(S) WITH ISSUES'}`);
process.exit(bad ? 1 : 0);
