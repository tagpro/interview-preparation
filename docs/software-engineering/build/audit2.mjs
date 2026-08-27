import { chromium } from 'playwright';
const base='file:///tmp/claude-0/-home-user-itineraries/743066b5-f723-51f2-b6f0-b1bc64e095c2/scratchpad/';
const files=process.argv.slice(2).length?process.argv.slice(2):
  ['backend-go-ladder.html','pillar-a-foundations.html','pillar-b-go.html','pillar-c-cloud.html'];
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let total=0;
for (const f of files) {
  const p = await b.newPage({ viewport:{width:1440,height:1000}, colorScheme:'light' });
  await p.goto(base+f); await p.waitForTimeout(900);
  const res = await p.evaluate(() => {
    const out=[];
    document.querySelectorAll('figure svg').forEach((svg, si) => {
      const vb=svg.viewBox.baseVal, issues=[];
      const T=[...svg.querySelectorAll('text')].map(t=>{let bb;try{bb=t.getBBox()}catch(e){return null}
        return {x:bb.x,y:bb.y,w:bb.width,h:bb.height,s:(t.textContent||'').trim().slice(0,38)}}).filter(Boolean);
      const R=[...svg.querySelectorAll('rect')].map(r=>{let bb;try{bb=r.getBBox()}catch(e){return null}
        return {x:bb.x,y:bb.y,w:bb.width,h:bb.height}}).filter(Boolean);
      const L=[...svg.querySelectorAll('line,polyline,path')].filter(e=>!e.closest('marker'))
        .map(l=>{let bb;try{bb=l.getBBox()}catch(e){return null}
        return {x:bb.x,y:bb.y,w:bb.width,h:bb.height,tag:l.tagName}}).filter(Boolean);

      // viewBox overflow
      T.forEach(t=>{const o=[];
        if(t.x<vb.x-1)o.push('left');
        if(t.x+t.w>vb.x+vb.width+1)o.push('right+'+Math.round(t.x+t.w-vb.width));
        if(t.y+t.h>vb.y+vb.height+1)o.push('bottom+'+Math.round(t.y+t.h-vb.height));
        if(o.length)issues.push({k:'CLIPPED',dir:o.join(','),t:t.s});});

      // text-text overlap
      for(let i=0;i<T.length;i++)for(let j=i+1;j<T.length;j++){const a=T[i],c=T[j];
        const ox=Math.min(a.x+a.w,c.x+c.w)-Math.max(a.x,c.x), oy=Math.min(a.y+a.h,c.y+c.h)-Math.max(a.y,c.y);
        const sameRow = oy > 0.6*Math.min(a.h,c.h);
        if(sameRow && ox > -6){ issues.push({k:'TEXT-COLLIDE',gap:Math.round(-ox),a:a.s,b:c.s}); }
        else if(ox>1.5&&oy>1.5){const r=ox*oy/Math.min(a.w*a.h,c.w*c.h);
          if(r>0.14)issues.push({k:'TEXT-OVERLAP',pct:Math.round(r*100),a:a.s,b:c.s});}}

      // text spilling out of its own box
      T.forEach(t=>{
        const cands=R.filter(r=>t.x>=r.x-3&&t.x<r.x+r.w&&t.y-t.h*0.6>=r.y-3&&t.y<=r.y+r.h+3&&r.w>20&&r.h>10);
        if(!cands.length)return;
        cands.sort((p,q)=>p.w*p.h-q.w*q.h);
        const r=cands[0];
        if(t.x+t.w>r.x+r.w-2) issues.push({k:'TEXT>BOX',over:Math.round(t.x+t.w-(r.x+r.w)),t:t.s});
      });

      // a line running through the middle of a text run
      const plated=[...svg.querySelectorAll('rect.plate')].map(r=>r.getBBox());
      const inPlate=t=>plated.some(r=>t.x>=r.x-3&&t.x+t.w<=r.x+r.width+6&&t.y>=r.y-4&&t.y+t.h<=r.y+r.height+6);
      T.forEach(t=>{ if(inPlate(t)) return; L.forEach(l=>{
        if(l.h<2.5 && l.w>8){ const y=l.y+l.h/2;
          if(y>t.y+2.5 && y<t.y+t.h-2.5){
            const ox=Math.min(l.x+l.w,t.x+t.w)-Math.max(l.x,t.x);
            if(ox>t.w*0.5) issues.push({k:'LINE-THRU',t:t.s});}}
        if(l.w<2.5 && l.h>8){ const x=l.x+l.w/2;
          if(x>t.x+3 && x<t.x+t.w-3){
            const oy=Math.min(l.y+l.h,t.y+t.h)-Math.max(l.y,t.y);
            if(oy>t.h*0.5) issues.push({k:'LINE-THRU-V',t:t.s});}}
      });});

      if(issues.length){
        const seen=new Set(), uniq=[];
        issues.forEach(i=>{const k=JSON.stringify(i); if(!seen.has(k)){seen.add(k);uniq.push(i);}});
        out.push({si,label:(svg.getAttribute('aria-label')||'').slice(0,48),issues:uniq});
      }
    });
    return out;
  });
  for(const r of res){ console.log('\n== '+f+' #'+r.si+'  '+r.label);
    r.issues.forEach(i=>{total++; console.log('    '+JSON.stringify(i));}); }
  await p.close();
}
await b.close();
console.log('\nTOTAL: '+total);
