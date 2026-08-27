import { chromium } from 'playwright';
const base='file:///tmp/claude-0/-home-user-itineraries/743066b5-f723-51f2-b6f0-b1bc64e095c2/scratchpad/';
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const p=await b.newPage({viewport:{width:1440,height:900},colorScheme:'dark'});
const errs=[]; p.on('pageerror',e=>errs.push(e.message));
await p.goto(base+'java-spring.html'); await p.waitForTimeout(700);
console.log(JSON.stringify(await p.evaluate(()=>{
  const toc=document.getElementById('toc'), cs=getComputedStyle(toc);
  const prog=document.querySelector('.topbar .progress');
  return {
    tocPosition: cs.position, tocRight: cs.right, tocWidth: cs.width,
    bodyPadRight: getComputedStyle(document.body).paddingRight,
    progressExists: !!prog, progressHeight: prog?getComputedStyle(prog).height:null,
    tocItems: document.querySelectorAll('.toc ol a').length,
    series: document.querySelectorAll('.toc-series a').length,
    here: document.querySelectorAll('.toc-series a.here').length,
    hscroll: document.documentElement.scrollWidth>window.innerWidth+2
  };}),null,1));
await p.evaluate(()=>window.scrollTo(0,4000)); await p.waitForTimeout(400);
console.log('pct', await p.textContent('#pct'), '| active', await p.textContent('.toc ol a.active'));
await p.screenshot({path:'shots/java-page.png'});
console.log('errors', errs.length?errs:'none');
await b.close();
