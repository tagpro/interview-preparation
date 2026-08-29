# -*- coding: utf-8 -*-
"""Page-level chrome unique to the algorithms page: a three-way language switch
and the chrome around the interactive figures.

The switch works the way the AWS page's does -- every language-specific block
carries data-lang="go", "py" or "java", the root element carries lang-go /
lang-py / lang-java, and CSS hides the other two. With JavaScript off all three
are simply visible, which is a working page rather than a blank one. The choice
is stored under the series' own key, so a reader who picked Python here keeps
Python on the AWS page (which knows only Go and Python, and falls back to Go for
a reader who picked Java).

The demo chrome is deliberately thin: a head with a title and controls, a stage
the demo paints into, and a readout line. Everything the demos draw is ordinary
DOM or SVG rather than a canvas, so it survives Ctrl-P.
"""

CSS = """
<style>
/* ---------- language switch ---------- */
.langbar{display:inline-flex;border:1px solid var(--line);background:var(--surface);
  flex:0 0 auto;align-items:stretch}
.langbar button{
  font-family:"IBM Plex Mono",monospace;font-size:0.68rem;letter-spacing:0.09em;
  text-transform:uppercase;background:transparent;color:var(--ink-faint);
  border:0;border-right:1px solid var(--line);padding:6px 11px;cursor:pointer;white-space:nowrap;
}
.langbar button:last-child{border-right:0}
.langbar button:hover{color:var(--ink)}
.langbar button[aria-pressed="true"]{background:var(--accent);color:var(--ground);font-weight:600}
:root.lang-go [data-lang="py"],:root.lang-go [data-lang="java"]{display:none}
:root.lang-py [data-lang="go"],:root.lang-py [data-lang="java"]{display:none}
:root.lang-java [data-lang="go"],:root.lang-java [data-lang="py"]{display:none}
.langnote{font-family:"IBM Plex Mono",monospace;font-size:0.66rem;letter-spacing:0.08em;
  text-transform:uppercase;color:var(--ink-faint);margin:20px 0 -8px}
.langnote b{color:var(--accent);font-weight:600}
pre + pre[data-lang]{margin-top:18px}
/* the switch is the point of this page, so on a narrow bar it keeps its room */
.m-short{display:none}
@media (max-width:760px){
  .topbar-in{gap:12px}
  .topbar .progress,.topbar .pct{display:none}
  .m-full{display:none}
  .m-short{display:inline}
}

/* ---------- the small fact grid the series uses ---------- */
.svc{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:0;
  border:1px solid var(--line);background:var(--surface);margin:24px 0}
.svc div{padding:13px 16px;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
.svc div:last-child{border-right:none}
.svc .h{font-family:"IBM Plex Mono",monospace;font-size:0.66rem;letter-spacing:0.1em;
  text-transform:uppercase;color:var(--ink-faint);display:block;margin-bottom:5px}
.svc .b{font-size:0.88rem;color:var(--ink-soft);line-height:1.45}
.svc .b b{color:var(--ink);font-weight:600}
@media (max-width:640px){.svc div{border-right:none}}

/* ---------- complexity badges ---------- */
.big{font-family:"IBM Plex Mono",monospace;font-weight:600;white-space:nowrap;
  font-size:0.9em;padding:0.05em 0.4em;border:1px solid var(--line);background:var(--surface-2)}
.big.g{color:var(--l1)} .big.a{color:var(--l2)} .big.b{color:var(--l3)}
td .big,th .big{font-size:0.82em}

/* ---------- interactive figures ---------- */
figure.demo{padding:0;overflow:visible}
.demo-head{display:flex;flex-wrap:wrap;gap:9px 16px;align-items:center;
  justify-content:space-between;padding:11px 14px;border-bottom:1px solid var(--line);
  background:var(--surface-2)}
.demo-title{font-family:"IBM Plex Mono",monospace;font-size:0.66rem;letter-spacing:0.1em;
  text-transform:uppercase;color:var(--ink-faint);font-weight:600}
.demo-ctl{display:flex;flex-wrap:wrap;gap:7px;align-items:center}
.demo-ctl button,.demo-ctl select{
  font-family:"IBM Plex Mono",monospace;font-size:0.68rem;letter-spacing:0.06em;
  background:var(--surface);color:var(--ink-soft);border:1px solid var(--line);
  padding:5px 10px;cursor:pointer;line-height:1.2}
.demo-ctl select{padding:4px 6px}
.demo-ctl button:hover,.demo-ctl select:hover{color:var(--ink);border-color:var(--accent)}
.demo-ctl button[aria-pressed="true"]{background:var(--accent);color:var(--ground);
  border-color:var(--accent);font-weight:600}
.demo-ctl button:disabled{opacity:0.4;cursor:default}
.demo-ctl button:disabled:hover{color:var(--ink-soft);border-color:var(--line)}
.demo-ctl .seg{display:inline-flex}
.demo-ctl .seg button{border-right-width:0}
.demo-ctl .seg button:last-child{border-right-width:1px}
.demo-stage{padding:16px 14px;overflow-x:auto}
.demo-read{margin:0;padding:9px 14px;border-top:1px solid var(--line);background:var(--surface-2);
  font-family:"IBM Plex Mono",monospace;font-size:0.72rem;color:var(--ink-soft);line-height:1.55;
  min-height:2.2em}
.demo-read b{color:var(--ink);font-weight:600}
.demo-read .n{color:var(--accent);font-weight:600;font-variant-numeric:tabular-nums}
figure.demo figcaption{padding:0 14px 13px}
.demo-legend{display:flex;flex-wrap:wrap;gap:4px 16px;margin-top:12px;
  font-family:"IBM Plex Mono",monospace;font-size:0.65rem;letter-spacing:0.04em;color:var(--ink-faint)}
.demo-legend span{display:inline-flex;align-items:center;gap:6px}
.demo-legend i{width:10px;height:10px;display:inline-block;background:var(--k);
  border:1px solid var(--line)}

/* bars: the sorting stage */
.bars{display:flex;align-items:flex-end;gap:2px;height:180px}
.bars .bar{flex:1 1 0;min-width:3px;background:var(--ink-faint);position:relative}
.bars .bar.ok{background:var(--l1)}
.bars .bar.cmp{background:var(--l2)}
.bars .bar.mv{background:var(--l3)}
.bars .bar.piv{background:var(--l3);outline:2px solid var(--l3);outline-offset:1px}
.bars .bar.dim{opacity:0.34}

/* cells: arrays, hash buckets, DP rows */
.cells{display:flex;flex-wrap:wrap;gap:3px;align-items:flex-start}
.cell{min-width:32px;height:32px;padding:0 5px;border:1px solid var(--line);background:var(--surface);
  display:flex;align-items:center;justify-content:center;
  font-family:"IBM Plex Mono",monospace;font-size:0.76rem;color:var(--ink);
  font-variant-numeric:tabular-nums}
.cell.empty{color:var(--ink-faint);background:var(--surface-2);border-style:dashed}
.cell.hit{border-color:var(--l1);color:var(--l1);font-weight:600}
.cell.on{border-color:var(--l2);color:var(--l2);font-weight:600}
.cell.warn{border-color:var(--l3);color:var(--l3);font-weight:600}
.cell.out{opacity:0.32}
.idx{display:flex;flex-wrap:wrap;gap:3px;margin-top:4px}
.idx span{min-width:32px;padding:0 5px;text-align:center;font-family:"IBM Plex Mono",monospace;
  font-size:0.62rem;color:var(--ink-faint);font-variant-numeric:tabular-nums}
.ptr{display:flex;flex-wrap:wrap;gap:3px;margin-bottom:4px;height:1.1em}
.ptr span{min-width:32px;padding:0 5px;text-align:center;font-family:"IBM Plex Mono",monospace;
  font-size:0.66rem;font-weight:600;line-height:1.1}

/* rows of labelled cells: hash buckets, union-find, DP */
.rows{display:grid;gap:3px}
.rows.tight{gap:2px}
.rows.tight .cell{height:25px;min-width:28px}
.row{display:flex;gap:6px;align-items:center}
.row .lab{min-width:74px;font-family:"IBM Plex Mono",monospace;font-size:0.66rem;
  color:var(--ink-faint);text-align:right;flex:0 0 auto}

/* grid: the pathfinding stage */
.grid{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);width:max-content}
.grid b{width:var(--cs,17px);height:var(--cs,17px);background:var(--surface);display:block;
  cursor:pointer;font-weight:400}
.grid b.wall{background:var(--ink-soft);cursor:pointer}
.grid b.seen{background:color-mix(in srgb,var(--l2) 26%,var(--surface))}
.grid b.frontier{background:var(--l2);}
.grid b.path{background:var(--l1)}
.grid b.src{background:var(--l1);box-shadow:inset 0 0 0 2px var(--ground)}
.grid b.dst{background:var(--l3);box-shadow:inset 0 0 0 2px var(--ground)}
.grid b.slow{background:var(--surface-2);box-shadow:inset 0 0 0 1px var(--line)}
.grid b.slow.seen{background:color-mix(in srgb,var(--l2) 26%,var(--surface-2))}

/* dp table */
.dp{border-collapse:collapse;font-family:"IBM Plex Mono",monospace;font-size:0.72rem;
  min-width:0;width:auto}
.dp td,.dp th{border:1px solid var(--line);padding:3px 6px;text-align:center;min-width:28px;
  color:var(--ink-faint);font-variant-numeric:tabular-nums;background:transparent}
.dp th{font-size:0.7rem;color:var(--ink);font-weight:600;letter-spacing:0;text-transform:none;
  font-family:"IBM Plex Mono",monospace;background:transparent}
.dp td.set{color:var(--ink)}
.dp td.now{background:var(--l2);color:var(--ground);font-weight:600}
.dp td.dep{box-shadow:inset 0 0 0 2px var(--l3)}
.dp td.trace{background:var(--l1);color:var(--ground);font-weight:600}

/* svg stages: trees, heaps, forests */
.demo-stage svg{display:block;width:100%;height:auto;color:var(--ink);overflow:visible}
.demo-stage svg text{font-family:"IBM Plex Mono",monospace;font-size:11px;fill:currentColor}
.demo-stage svg .node circle,.demo-stage svg .node rect{fill:var(--surface);stroke:currentColor;stroke-width:1.4}
.demo-stage svg .node.on circle,.demo-stage svg .node.on rect{fill:var(--l2);stroke:var(--l2)}
.demo-stage svg .node.on text{fill:var(--ground)}
.demo-stage svg .node.ok circle,.demo-stage svg .node.ok rect{fill:var(--l1);stroke:var(--l1)}
.demo-stage svg .node.ok text{fill:var(--ground)}
.demo-stage svg .node.hot circle,.demo-stage svg .node.hot rect{fill:var(--l3);stroke:var(--l3)}
.demo-stage svg .node.hot text{fill:var(--ground)}
.demo-stage svg .edge{stroke:var(--line);stroke-width:1.4;fill:none}
.demo-stage svg .edge.on{stroke:var(--l2);stroke-width:2}

/* the growth explorer */
.growth{display:grid;grid-template-columns:minmax(240px,1fr) minmax(240px,1.1fr);gap:22px;align-items:start}
/* grid items default to min-width:auto, so a wide table pushes the whole
   figure past the viewport instead of shrinking. */
.growth > *{min-width:0}
@media (max-width:720px){.growth{grid-template-columns:1fr}}
.growth input[type=range]{width:100%;accent-color:var(--accent)}
.gtab{width:100%;border-collapse:collapse;font-size:0.78rem;min-width:0}
.gtab td,.gtab th{border-bottom:1px solid var(--line);padding:5px 6px;text-align:right;
  font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;color:var(--ink-soft)}
/* only the growth label must stay on one line -- "O(n log n)" broken across two
   rows reads as two different bounds */
.gtab td:first-child,.gtab th:first-child{white-space:nowrap}
.gtab th{text-align:right;font-size:0.64rem;letter-spacing:0.08em;text-transform:uppercase;
  color:var(--ink-faint);background:transparent}
.gtab td:first-child,.gtab th:first-child{text-align:left;color:var(--ink);font-weight:600}
.gtab tr.hot td{color:var(--l3)}
.gtab tr.fine td{color:var(--l1)}

/* a free-text input where a demo takes a word or a key */
.demo-ctl input[type=text]{font-family:"IBM Plex Mono",monospace;font-size:0.72rem;
  background:var(--surface);color:var(--ink);border:1px solid var(--line);padding:5px 7px;width:9ch}
.demo-ctl input[type=text]:focus{border-color:var(--accent);outline:none}
.demo-ctl label{font-family:"IBM Plex Mono",monospace;font-size:0.66rem;color:var(--ink-faint);
  letter-spacing:0.06em;display:inline-flex;align-items:center;gap:5px}
.nojs{font-size:0.85rem;color:var(--ink-faint);margin:0}
</style>
"""

EARLY_JS = """
<script>
(function(){var l="go";try{var v=localStorage.getItem("ladder-lang");
if(v==="py"||v==="go"||v==="java")l=v;}catch(e){}
document.documentElement.classList.add("lang-"+l);})();
</script>
"""

BAR = """    <div class="langbar" role="group" aria-label="Code language">
      <button type="button" data-set="go" aria-pressed="true">Go</button>
      <button type="button" data-set="py" aria-pressed="false">Python</button>
      <button type="button" data-set="java" aria-pressed="false">Java</button>
    </div>
"""

JS = """
<script>
(function(){
  "use strict";
  var root = document.documentElement;
  var btns = Array.prototype.slice.call(document.querySelectorAll(".langbar button"));
  if (!btns.length) return;
  var KEYS = { g: "go", p: "py", j: "java" };

  function paint(l){
    root.classList.remove("lang-go", "lang-py", "lang-java");
    root.classList.add("lang-" + l);
    btns.forEach(function(b){
      b.setAttribute("aria-pressed", b.getAttribute("data-set") === l ? "true" : "false");
    });
  }

  /* switching hides or reveals a few thousand lines of code, so the page height
     changes under the reader. Pin the topic they are looking at instead. */
  function anchor(){
    var els = document.querySelectorAll(".topic, .part");
    for (var i = els.length - 1; i >= 0; i--){
      var t = els[i].getBoundingClientRect().top;
      if (t <= 120) return { el: els[i], top: t };
    }
    return null;
  }

  paint(root.classList.contains("lang-py") ? "py"
      : root.classList.contains("lang-java") ? "java" : "go");

  btns.forEach(function(b){
    b.addEventListener("click", function(){
      var l = b.getAttribute("data-set");
      var a = anchor();
      paint(l);
      try { localStorage.setItem("ladder-lang", l); } catch (e) {}
      if (a) window.scrollTo(0, window.scrollY + (a.el.getBoundingClientRect().top - a.top));
      window.dispatchEvent(new Event("resize"));   /* progress bar + rail recompute */
    });
  });

  document.addEventListener("keydown", function(e){
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return;
    var target = KEYS[e.key];
    if (!target) return;
    var hit = btns.filter(function(b){ return b.getAttribute("data-set") === target; })[0];
    if (hit) hit.click();
  });
})();
</script>
"""
