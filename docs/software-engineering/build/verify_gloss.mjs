import { chromium } from 'playwright';
const base='file:///tmp/claude-0/-home-user-itineraries/743066b5-f723-51f2-b6f0-b1bc64e095c2/scratchpad/';
const files=['backend-go-ladder.html','pillar-a-foundations.html','pillar-b-go.html',
             'pillar-c-cloud.html','python-foundations.html','java-spring.html','aws-deep-dive.html'];
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
for(const f of files){
  const p=await b.newPage({viewport:{width:1440,height:900}});
  const errs=[]; p.on('pageerror',e=>errs.push('js: '+e.message));
  await p.goto(base+f); await p.waitForTimeout(700);

  const stat=await p.evaluate(()=>{
    const gl=[...document.querySelectorAll('abbr.gl')];
    const sv=[...document.querySelectorAll('text.gl-svg')];
    const bad=gl.filter(a=>a.closest('pre')||a.closest('svg')||a.closest('#toc')||a.closest('.topbar'));
    const terms=new Set(gl.map(a=>a.textContent));
    return {count:gl.length, svgLabels:sv.length, distinct:terms.size, misplaced:bad.length,
            sample:gl.slice(0,4).map(a=>a.textContent+'='+a.getAttribute('data-full'))};
  });

  // hover
  let hover='n/a', click='n/a', esc='n/a', kbd='n/a';
  if(stat.count){
    const first=p.locator('abbr.gl').first();
    await first.scrollIntoViewIfNeeded();
    await first.hover(); await p.waitForTimeout(250);
    hover=await p.evaluate(()=>{const t=document.getElementById('gloss');
      return t.classList.contains('on') ? t.innerText.replace(/\n/g,' | ').slice(0,70) : 'HIDDEN';});
    // click pins
    await first.click(); await p.waitForTimeout(150);
    click=await p.evaluate(()=>document.getElementById('gloss').classList.contains('on')?'pinned':'NOT PINNED');
    await p.keyboard.press('Escape'); await p.waitForTimeout(150);
    esc=await p.evaluate(()=>document.getElementById('gloss').classList.contains('on')?'STILL OPEN':'closed');
    // keyboard focus
    await p.evaluate(()=>{document.activeElement&&document.activeElement.blur();}); await p.waitForTimeout(150);
    await p.evaluate(()=>document.querySelector('abbr.gl').focus()); await p.waitForTimeout(250);
    kbd=await p.evaluate(()=>document.getElementById('gloss').classList.contains('on')?'shown':'NOT SHOWN');
    await p.evaluate(()=>document.querySelector('abbr.gl').blur()); await p.waitForTimeout(200);
  }
  const after=await p.evaluate(()=>({
    hscroll:document.documentElement.scrollWidth>window.innerWidth+2,
    toc:document.querySelectorAll('.toc ol a').length,
    series:document.querySelectorAll('.toc-series a').length}));
  console.log(f.padEnd(26), JSON.stringify({...stat, hover, click, esc, kbd, ...after}));
  if(errs.length) console.log('   ERRORS', errs);
  await p.close();
}
await b.close();
