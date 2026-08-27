# -*- coding: utf-8 -*-
"""Page-level chrome unique to the AWS deep dive: the Go/Python language switch.

Every language-specific block carries data-lang="go" or data-lang="py". The root
element carries lang-go / lang-py and the CSS hides the other one, so with
JavaScript off both languages are simply visible -- a working fallback rather
than a blank page. The choice is stored under the same key the whole series
would use, so a reader who picks Python keeps it across visits.
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
:root.lang-go [data-lang="py"]{display:none}
:root.lang-py [data-lang="go"]{display:none}
.langnote{font-family:"IBM Plex Mono",monospace;font-size:0.66rem;letter-spacing:0.08em;
  text-transform:uppercase;color:var(--ink-faint);margin:20px 0 -8px}
.langnote b{color:var(--accent);font-weight:600}
/* two stacked snippets that are the same program in both languages */
pre + pre[data-lang]{margin-top:18px}
.svc{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:0;
  border:1px solid var(--line);background:var(--surface);margin:24px 0}
.svc div{padding:13px 16px;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
.svc div:last-child{border-right:none}
.svc .h{font-family:"IBM Plex Mono",monospace;font-size:0.66rem;letter-spacing:0.1em;
  text-transform:uppercase;color:var(--ink-faint);display:block;margin-bottom:5px}
.svc .b{font-size:0.88rem;color:var(--ink-soft);line-height:1.45}
.svc .b b{color:var(--ink);font-weight:600}
@media (max-width:640px){.svc div{border-right:none}}
/* the switch is the point of this page, so on a narrow bar it keeps its room:
   the progress readout goes, the control stays where a thumb can reach it */
.m-short{display:none}
@media (max-width:720px){
  .topbar-in{gap:12px}
  .topbar .progress,.topbar .pct{display:none}
  .m-full{display:none}
  .m-short{display:inline}
}
</style>
"""

EARLY_JS = """
<script>
(function(){var l="go";try{var v=localStorage.getItem("ladder-lang");if(v==="py"||v==="go")l=v;}catch(e){}
document.documentElement.classList.add("lang-"+l);})();
</script>
"""

BAR = """    <div class="langbar" role="group" aria-label="Code language">
      <button type="button" data-set="go" aria-pressed="true">Go</button>
      <button type="button" data-set="py" aria-pressed="false">Python</button>
    </div>
"""

JS = """
<script>
(function(){
  "use strict";
  var root = document.documentElement;
  var btns = Array.prototype.slice.call(document.querySelectorAll(".langbar button"));
  if (!btns.length) return;

  function paint(l){
    root.classList.remove("lang-go", "lang-py");
    root.classList.add("lang-" + l);
    btns.forEach(function(b){
      b.setAttribute("aria-pressed", b.getAttribute("data-set") === l ? "true" : "false");
    });
  }

  /* switching hides or reveals a few hundred lines of code, so the page height
     changes under the reader. Pin the topic they are looking at instead. */
  function anchor(){
    var els = document.querySelectorAll(".topic, .part");
    for (var i = els.length - 1; i >= 0; i--){
      var t = els[i].getBoundingClientRect().top;
      if (t <= 120) return { el: els[i], top: t };
    }
    return null;
  }

  paint(root.classList.contains("lang-py") ? "py" : "go");

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
    if (tag === "input" || tag === "textarea") return;
    if (e.key === "g" || e.key === "p"){
      var target = e.key === "g" ? "go" : "py";
      var hit = btns.filter(function(b){ return b.getAttribute("data-set") === target; })[0];
      if (hit) hit.click();
    }
  });
})();
</script>
"""
