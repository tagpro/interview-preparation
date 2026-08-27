import { chromium } from 'playwright';
const base = 'file:///tmp/claude-0/-home-user-itineraries/743066b5-f723-51f2-b6f0-b1bc64e095c2/scratchpad/';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const p = await b.newPage({ viewport: { width: 1440, height: 900 }, colorScheme: 'dark' });
const errs = []; p.on('pageerror', e => errs.push(e.message));
p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });

await p.goto(base + 'aws-deep-dive.html');
await p.waitForTimeout(800);

const shape = await p.evaluate(() => {
  const toc = document.getElementById('toc');
  const vis = sel => [...document.querySelectorAll(sel)].filter(e => e.offsetParent !== null).length;
  return {
    tocItems: document.querySelectorAll('.toc ol a').length,
    parts: document.querySelectorAll('.part').length,
    topics: document.querySelectorAll('.topic').length,
    svgs: document.querySelectorAll('figure svg').length,
    series: document.querySelectorAll('.toc-series a').length,
    here: document.querySelectorAll('.toc-series a.here').length,
    tocPosition: getComputedStyle(toc).position,
    progressExists: !!document.querySelector('.topbar .progress'),
    langButtons: document.querySelectorAll('.langbar button').length,
    rootClass: document.documentElement.className,
    goBlocksTotal: document.querySelectorAll('[data-lang="go"]').length,
    pyBlocksTotal: document.querySelectorAll('[data-lang="py"]').length,
    goVisible: vis('[data-lang="go"]'),
    pyVisible: vis('[data-lang="py"]'),
    hscroll: document.documentElement.scrollWidth > window.innerWidth + 2,
  };
});
console.log('default (go):', JSON.stringify(shape, null, 1));

// switch to Python
await p.click('.langbar button[data-set="py"]');
await p.waitForTimeout(300);
const after = await p.evaluate(() => {
  const vis = sel => [...document.querySelectorAll(sel)].filter(e => e.offsetParent !== null).length;
  return {
    rootClass: document.documentElement.className,
    goVisible: vis('[data-lang="go"]'),
    pyVisible: vis('[data-lang="py"]'),
    pressed: [...document.querySelectorAll('.langbar button')].map(x => x.getAttribute('aria-pressed')),
    stored: (() => { try { return localStorage.getItem('ladder-lang'); } catch (e) { return 'blocked'; } })(),
    hscroll: document.documentElement.scrollWidth > window.innerWidth + 2,
  };
});
console.log('after switch (py):', JSON.stringify(after, null, 1));

// persistence across reload
await p.reload();
await p.waitForTimeout(600);
console.log('after reload:', await p.evaluate(() => document.documentElement.className));

// keyboard shortcut back to Go
await p.keyboard.press('g');
await p.waitForTimeout(200);
console.log('after key g:', await p.evaluate(() => document.documentElement.className));

// scroll behaviour: progress + active section
await p.evaluate(() => window.scrollTo(0, 12000));
await p.waitForTimeout(400);
console.log('pct', await p.textContent('#pct'), '| active', await p.textContent('.toc ol a.active'));

// no horizontal scroll on a narrow viewport either, in both languages
const narrow = await b.newPage({ viewport: { width: 390, height: 844 }, colorScheme: 'light' });
await narrow.goto(base + 'aws-deep-dive.html');
await narrow.waitForTimeout(600);
console.log('mobile hscroll go:', await narrow.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2));
await narrow.click('.langbar button[data-set="py"]');
await narrow.waitForTimeout(300);
console.log('mobile hscroll py:', await narrow.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2));

await p.screenshot({ path: 'shots/aws-page.png' });
console.log('errors', errs.length ? errs : 'none');
await b.close();
