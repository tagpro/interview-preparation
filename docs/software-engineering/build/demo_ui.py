# -*- coding: utf-8 -*-
"""The pieces an interactive page needs, shared by every page that has one.

Two pages in the series now carry figures that run -- the algorithms page and
the AI engineering page -- and before this module existed the second one would
have started life as a copy of the first one's player and chrome. That is the
same mistake the cross-link rail made before series.py: two copies of a thing
that must stay identical, drifting a little at a time.

So the player, the chrome around a figure, and the language switch live here.
A page supplies its own stage CSS (bars and grids on one page, matrices and
token chips on the other) and its own demos; everything else comes from here.

The player itself is documented where it is defined, in PLAYER_JS below. The
short version: every demo is a *trace*, precomputed, so the reader can step
backwards and the opening state is deterministic -- which is what lets the
print pass render the same ink twice.
"""

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

# The fixed half of the language switch: the bar itself, the note above a
# snippet pair, and the narrow-screen rule that shrinks the page name so the
# switch keeps its place.
_SWITCH_HEAD = '/* ---------- language switch ---------- */\n.langbar{display:inline-flex;border:1px solid var(--line);background:var(--surface);\n  flex:0 0 auto;align-items:stretch}\n.langbar button{\n  font-family:"IBM Plex Mono",monospace;font-size:0.68rem;letter-spacing:0.09em;\n  text-transform:uppercase;background:transparent;color:var(--ink-faint);\n  border:0;border-right:1px solid var(--line);padding:6px 11px;cursor:pointer;white-space:nowrap;\n}\n.langbar button:last-child{border-right:0}\n.langbar button:hover{color:var(--ink)}\n.langbar button[aria-pressed="true"]{background:var(--accent);color:var(--ground);font-weight:600}\n'

_SWITCH_TAIL = '.langnote{font-family:"IBM Plex Mono",monospace;font-size:0.66rem;letter-spacing:0.08em;\n  text-transform:uppercase;color:var(--ink-faint);margin:20px 0 -8px}\n.langnote b{color:var(--accent);font-weight:600}\npre + pre[data-lang]{margin-top:18px}\n/* the switch is the point of this page, so on a narrow bar it keeps its room */\n.m-short{display:none}\n@media (max-width:760px){\n  .topbar-in{gap:12px}\n  .topbar .progress,.topbar .pct{display:none}\n  .m-full{display:none}\n  .m-short{display:inline}\n}\n\n'


def switch_css(prefix, codes):
    """The switch, for a page whose root carries `<prefix>-<code>` classes.

    The two pages use different prefixes and different language sets on
    purpose: they store the reader's choice under different keys, so picking
    TypeScript on one page does not select a language the other does not have.
    """
    rules = '\n'.join(
        ','.join(':root.%s-%s [data-lang="%s"]' % (prefix, c, o) for o in codes if o != c)
        + '{display:none}'
        for c in codes)
    return _SWITCH_HEAD + rules + '\n' + _SWITCH_TAIL


# The small fact grid, the inline mono badge, and the chrome around a figure:
# head, controls, stage, readout, caption, legend.
FACTS = '/* ---------- the small fact grid the series uses ---------- */\n.svc{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:0;\n  border:1px solid var(--line);background:var(--surface);margin:24px 0}\n.svc div{padding:13px 16px;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}\n.svc div:last-child{border-right:none}\n.svc .h{font-family:"IBM Plex Mono",monospace;font-size:0.66rem;letter-spacing:0.1em;\n  text-transform:uppercase;color:var(--ink-faint);display:block;margin-bottom:5px}\n.svc .b{font-size:0.88rem;color:var(--ink-soft);line-height:1.45}\n.svc .b b{color:var(--ink);font-weight:600}\n@media (max-width:640px){.svc div{border-right:none}}\n\n'

BADGES = '/* ---------- complexity badges ---------- */\n.big{font-family:"IBM Plex Mono",monospace;font-weight:600;white-space:nowrap;\n  font-size:0.9em;padding:0.05em 0.4em;border:1px solid var(--line);background:var(--surface-2)}\n.big.g{color:var(--l1)} .big.a{color:var(--l2)} .big.b{color:var(--l3)}\ntd .big,th .big{font-size:0.82em}\n\n'

CHROME = '/* ---------- interactive figures ---------- */\nfigure.demo{padding:0;overflow:visible}\n.demo-head{display:flex;flex-wrap:wrap;gap:9px 16px;align-items:center;\n  justify-content:space-between;padding:11px 14px;border-bottom:1px solid var(--line);\n  background:var(--surface-2)}\n.demo-title{font-family:"IBM Plex Mono",monospace;font-size:0.66rem;letter-spacing:0.1em;\n  text-transform:uppercase;color:var(--ink-faint);font-weight:600}\n.demo-ctl{display:flex;flex-wrap:wrap;gap:7px;align-items:center}\n.demo-ctl button,.demo-ctl select{\n  font-family:"IBM Plex Mono",monospace;font-size:0.68rem;letter-spacing:0.06em;\n  background:var(--surface);color:var(--ink-soft);border:1px solid var(--line);\n  padding:5px 10px;cursor:pointer;line-height:1.2}\n.demo-ctl select{padding:4px 6px}\n.demo-ctl button:hover,.demo-ctl select:hover{color:var(--ink);border-color:var(--accent)}\n.demo-ctl button[aria-pressed="true"]{background:var(--accent);color:var(--ground);\n  border-color:var(--accent);font-weight:600}\n.demo-ctl button:disabled{opacity:0.4;cursor:default}\n.demo-ctl button:disabled:hover{color:var(--ink-soft);border-color:var(--line)}\n.demo-ctl .seg{display:inline-flex}\n.demo-ctl .seg button{border-right-width:0}\n.demo-ctl .seg button:last-child{border-right-width:1px}\n.demo-stage{padding:16px 14px;overflow-x:auto}\n.demo-read{margin:0;padding:9px 14px;border-top:1px solid var(--line);background:var(--surface-2);\n  font-family:"IBM Plex Mono",monospace;font-size:0.72rem;color:var(--ink-soft);line-height:1.55;\n  min-height:2.2em}\n.demo-read b{color:var(--ink);font-weight:600}\n.demo-read .n{color:var(--accent);font-weight:600;font-variant-numeric:tabular-nums}\nfigure.demo figcaption{padding:0 14px 13px}\n.demo-legend{display:flex;flex-wrap:wrap;gap:4px 16px;margin-top:12px;\n  font-family:"IBM Plex Mono",monospace;font-size:0.65rem;letter-spacing:0.04em;color:var(--ink-faint)}\n.demo-legend span{display:inline-flex;align-items:center;gap:6px}\n.demo-legend i{width:10px;height:10px;display:inline-block;background:var(--k);\n  border:1px solid var(--line)}\n\n'

# Stages more than one page draws into.
CELLS = '/* cells: arrays, hash buckets, DP rows */\n.cells{display:flex;flex-wrap:wrap;gap:3px;align-items:flex-start}\n.cell{min-width:32px;height:32px;padding:0 5px;border:1px solid var(--line);background:var(--surface);\n  display:flex;align-items:center;justify-content:center;\n  font-family:"IBM Plex Mono",monospace;font-size:0.76rem;color:var(--ink);\n  font-variant-numeric:tabular-nums}\n.cell.empty{color:var(--ink-faint);background:var(--surface-2);border-style:dashed}\n.cell.hit{border-color:var(--l1);color:var(--l1);font-weight:600}\n.cell.on{border-color:var(--l2);color:var(--l2);font-weight:600}\n.cell.warn{border-color:var(--l3);color:var(--l3);font-weight:600}\n.cell.out{opacity:0.32}\n.idx{display:flex;flex-wrap:wrap;gap:3px;margin-top:4px}\n.idx span{min-width:32px;padding:0 5px;text-align:center;font-family:"IBM Plex Mono",monospace;\n  font-size:0.62rem;color:var(--ink-faint);font-variant-numeric:tabular-nums}\n.ptr{display:flex;flex-wrap:wrap;gap:3px;margin-bottom:4px;height:1.1em}\n.ptr span{min-width:32px;padding:0 5px;text-align:center;font-family:"IBM Plex Mono",monospace;\n  font-size:0.66rem;font-weight:600;line-height:1.1}\n\n'

ROWS = '/* rows of labelled cells: hash buckets, union-find, DP */\n.rows{display:grid;gap:3px}\n.rows.tight{gap:2px}\n.rows.tight .cell{height:25px;min-width:28px}\n.row{display:flex;gap:6px;align-items:center}\n.row .lab{min-width:74px;font-family:"IBM Plex Mono",monospace;font-size:0.66rem;\n  color:var(--ink-faint);text-align:right;flex:0 0 auto}\n\n'

SVG = '/* svg stages: trees, heaps, forests */\n.demo-stage svg{display:block;width:100%;height:auto;color:var(--ink);overflow:visible}\n.demo-stage svg text{font-family:"IBM Plex Mono",monospace;font-size:11px;fill:currentColor}\n.demo-stage svg .node circle,.demo-stage svg .node rect{fill:var(--surface);stroke:currentColor;stroke-width:1.4}\n.demo-stage svg .node.on circle,.demo-stage svg .node.on rect{fill:var(--l2);stroke:var(--l2)}\n.demo-stage svg .node.on text{fill:var(--ground)}\n.demo-stage svg .node.ok circle,.demo-stage svg .node.ok rect{fill:var(--l1);stroke:var(--l1)}\n.demo-stage svg .node.ok text{fill:var(--ground)}\n.demo-stage svg .node.hot circle,.demo-stage svg .node.hot rect{fill:var(--l3);stroke:var(--l3)}\n.demo-stage svg .node.hot text{fill:var(--ground)}\n.demo-stage svg .edge{stroke:var(--line);stroke-width:1.4;fill:none}\n.demo-stage svg .edge.on{stroke:var(--l2);stroke-width:2}\n\n'

# A two-column figure body: a control on the left, a table on the right.
SPLIT = '/* the growth explorer */\n.growth{display:grid;grid-template-columns:minmax(240px,1fr) minmax(240px,1.1fr);gap:22px;align-items:start}\n/* grid items default to min-width:auto, so a wide table pushes the whole\n   figure past the viewport instead of shrinking. */\n.growth > *{min-width:0}\n@media (max-width:720px){.growth{grid-template-columns:1fr}}\n.growth input[type=range]{width:100%;accent-color:var(--accent)}\n.gtab{width:100%;border-collapse:collapse;font-size:0.78rem;min-width:0}\n.gtab td,.gtab th{border-bottom:1px solid var(--line);padding:5px 6px;text-align:right;\n  font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;color:var(--ink-soft)}\n/* only the growth label must stay on one line -- "O(n log n)" broken across two\n   rows reads as two different bounds */\n.gtab td:first-child,.gtab th:first-child{white-space:nowrap}\n.gtab th{text-align:right;font-size:0.64rem;letter-spacing:0.08em;text-transform:uppercase;\n  color:var(--ink-faint);background:transparent}\n.gtab td:first-child,.gtab th:first-child{text-align:left;color:var(--ink);font-weight:600}\n.gtab tr.hot td{color:var(--l3)}\n.gtab tr.fine td{color:var(--l1)}\n\n'

INPUTS = '/* a free-text input where a demo takes a word or a key */\n.demo-ctl input[type=text]{font-family:"IBM Plex Mono",monospace;font-size:0.72rem;\n  background:var(--surface);color:var(--ink);border:1px solid var(--line);padding:5px 7px;width:9ch}\n.demo-ctl input[type=text]:focus{border-color:var(--accent);outline:none}\n.demo-ctl label{font-family:"IBM Plex Mono",monospace;font-size:0.66rem;color:var(--ink-faint);\n  letter-spacing:0.06em;display:inline-flex;align-items:center;gap:5px}\n.nojs{font-size:0.85rem;color:var(--ink-faint);margin:0}\n'

# What every interactive page includes, in the order the sheet reads best.
def sheet(prefix, codes, *stages):
    """The page's whole figure stylesheet: shared chrome, then its own stages."""
    return '\n<style>\n' + switch_css(prefix, codes) + FACTS + BADGES + CHROME \
        + ''.join(stages) + INPUTS + '</style>\n'


# ---------------------------------------------------------------------------
# The switch behaviour
# ---------------------------------------------------------------------------

def early_js(prefix, key, codes, default):
    """Set the language class before first paint, so no pane flashes.

    This runs ahead of the topbar rather than with the rest of the behaviour:
    by the time the deferred script runs the browser has already painted, and
    a reader who chose Go would watch a screenful of Python disappear.
    """
    test = '||'.join('v==="%s"' % c for c in codes)
    return ('\n<script>\n(function(){var l="%s";try{var v=localStorage.getItem("%s");\n'
            'if(%s)l=v;}catch(e){}\n'
            'document.documentElement.classList.add("%s-"+l);})();\n</script>\n'
            % (default, key, test, prefix))


def bar(langs, default):
    """The switch itself: (code, label) pairs, one pressed."""
    out = ['    <div class="langbar" role="group" aria-label="Code language">']
    for code, label in langs:
        out.append('      <button type="button" data-set="%s" aria-pressed="%s">%s</button>'
                   % (code, 'true' if code == default else 'false', label))
    out.append('    </div>\n')
    return '\n'.join(out)


PLAYER_JS = '\n<script>\n(function () {\n  "use strict";\n\n  /* ==================================================================\n     The player\n     ================================================================== */\n\n  var REG = {};\n  function reg(name, factory) { REG[name] = factory; }\n\n  function el(tag, cls, txt) {\n    var e = document.createElement(tag);\n    if (cls) e.className = cls;\n    if (txt != null) e.textContent = txt;\n    return e;\n  }\n  function btn(label, title) {\n    var b = el("button", null, label);\n    b.type = "button";\n    if (title) b.title = title;\n    return b;\n  }\n  function sel(options, value) {\n    var s = document.createElement("select");\n    options.forEach(function (o) {\n      var op = document.createElement("option");\n      op.value = o[0]; op.textContent = o[1];\n      if (o[0] === value) op.selected = true;\n      s.appendChild(op);\n    });\n    return s;\n  }\n  function commas(n) { return String(Math.round(n)).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ","); }\n\n  var REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;\n\n  function mount(fig) {\n    var factory = REG[fig.getAttribute("data-demo")];\n    if (!factory) return;\n    var stage = fig.querySelector(".demo-stage");\n    var read = fig.querySelector(".demo-read");\n    var ctl = fig.querySelector(".demo-ctl");\n    if (!stage || !ctl) return;\n    ctl.innerHTML = "";\n    stage.innerHTML = "";\n\n    var frames = null, at = 0, timer = 0, playing = false, demo;\n    var play, prev, next;\n\n    var api = {\n      fig: fig, stage: stage, read: read, ctl: ctl,\n      speed: 130,\n      /* readout line under the stage */\n      say: function (html) { if (read) read.innerHTML = html; },\n      /* recompute the trace after a control changed */\n      rebuild: function (keepAt) {\n        stop();\n        frames = demo.frames ? demo.frames() : null;\n        at = !frames ? 0\n           : keepAt ? Math.min(at, frames.length - 1)\n           : demo.start ? Math.min(Math.max(0, demo.start(frames)), frames.length - 1)\n           : 0;\n        paint();\n      },\n      at: function () { return at; },\n      total: function () { return frames ? frames.length : 0; },\n      /* controls the demo owns, added left of the transport */\n      add: function (node) { ctl.appendChild(node); return node; },\n      button: btn, select: sel, el: el, commas: commas\n    };\n\n    demo = factory(api);\n\n    if (demo.frames) {\n      var seg = el("div", "seg nav");\n      prev = btn("◀", "Step back (left arrow)");\n      play = btn("Play", "Play or pause (space)");\n      next = btn("▶", "Step forward (right arrow)");\n      seg.appendChild(prev); seg.appendChild(play); seg.appendChild(next);\n      ctl.appendChild(seg);\n      var reset = btn("Reset");\n      ctl.appendChild(reset);\n\n      prev.addEventListener("click", function () { stop(); go(at - 1); });\n      next.addEventListener("click", function () { stop(); go(at + 1); });\n      reset.addEventListener("click", function () { stop(); go(0); });\n      play.addEventListener("click", function () { playing ? stop() : start(); });\n\n      fig.addEventListener("keydown", function (e) {\n        var tag = (e.target.tagName || "").toLowerCase();\n        if (tag === "input" || tag === "select" || tag === "textarea") return;\n        if (e.key === "ArrowRight") { stop(); go(at + 1); e.preventDefault(); }\n        else if (e.key === "ArrowLeft") { stop(); go(at - 1); e.preventDefault(); }\n        else if (e.key === " " || e.key === "Spacebar") {\n          if (e.target.tagName === "BUTTON") return;   /* let the button take it */\n          playing ? stop() : start(); e.preventDefault();\n        }\n      });\n    }\n\n    function go(i) {\n      if (!frames || !frames.length) return;\n      at = Math.max(0, Math.min(frames.length - 1, i));\n      paint();\n    }\n    function paint() {\n      if (frames) {\n        demo.render(frames[at], at, frames.length);\n        if (prev) prev.disabled = at === 0;\n        if (next) next.disabled = at === frames.length - 1;\n      } else {\n        demo.render();\n      }\n    }\n    function start() {\n      if (!frames) return;\n      if (at >= frames.length - 1) at = 0;\n      playing = true; play.textContent = "Pause"; play.setAttribute("aria-pressed", "true");\n      timer = setInterval(function () {\n        if (at >= frames.length - 1) { stop(); return; }\n        go(at + 1);\n      }, REDUCED ? Math.max(api.speed, 320) : api.speed);\n    }\n    function stop() {\n      playing = false;\n      if (play) { play.textContent = "Play"; play.setAttribute("aria-pressed", "false"); }\n      clearInterval(timer); timer = 0;\n    }\n\n    api.rebuild();\n  }\n\n'

BOOT_JS = '  /* ---------- boot ---------- */\n  function boot() {\n    Array.prototype.forEach.call(document.querySelectorAll("figure.demo[data-demo]"), function (f) {\n      f.tabIndex = 0;                    /* so the arrow keys and space reach it */\n      try { mount(f); }\n      catch (e) { if (window.console) console.error("demo " + f.getAttribute("data-demo"), e); }\n    });\n  }\n  if (document.readyState === "complete") boot();\n  else window.addEventListener("load", boot);\n})();\n</script>\n'


def switch_js(prefix, key, codes, keys):
    """Clicking the switch, and the single-key shortcuts.

    `keys` maps a keyboard key to a language code. Switching hides or reveals a
    few thousand lines of code, so the page height changes under the reader;
    the anchor logic pins whichever topic they were looking at.
    """
    classes = ' '.join('"%s-%s"' % (prefix, c) for c in codes).replace(' "', ', "')
    # the fallback is the first code, so the ladder tests the others in turn
    guess = '\n      : '.join(
        'root.classList.contains("%s-%s") ? "%s"' % (prefix, c, c) for c in codes[1:]
    ) + ' : "%s"' % codes[0]
    return """
<script>
(function(){
  "use strict";
  var root = document.documentElement;
  var btns = Array.prototype.slice.call(document.querySelectorAll(".langbar button"));
  if (!btns.length) return;
  var KEYS = %(keys)s;

  function paint(l){
    root.classList.remove(%(classes)s);
    root.classList.add("%(prefix)s-" + l);
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

  paint(%(guess)s);

  btns.forEach(function(b){
    b.addEventListener("click", function(){
      var l = b.getAttribute("data-set");
      var a = anchor();
      paint(l);
      try { localStorage.setItem("%(key)s", l); } catch (e) {}
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
""" % {'keys': '{ ' + ', '.join('%s: "%s"' % (k, v) for k, v in keys) + ' }',
       'classes': classes, 'prefix': prefix, 'guess': guess, 'key': key}
