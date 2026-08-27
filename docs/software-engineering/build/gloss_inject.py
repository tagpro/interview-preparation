# -*- coding: utf-8 -*-
"""Inject the abbreviation glossary into every built page in the series.

Runs over the finished HTML rather than the fragments, so one pass covers all
seven pages regardless of which build script (if any) produced them. Idempotent:
a page that already carries the marker is skipped, so re-running after a rebuild
is the intended workflow.

    python3 gloss_inject.py            # all pages
    python3 gloss_inject.py aws-deep-dive.html
"""
import json
import re
import sys

import gloss_terms

MARK = '<!-- glossary -->'

PAGES = [
    'backend-go-ladder.html',
    'pillar-a-foundations.html',
    'pillar-b-go.html',
    'pillar-c-cloud.html',
    'python-foundations.html',
    'java-spring.html',
    'aws-deep-dive.html',
]

ENTS = {'&rsquo;': '’', '&mdash;': '—', '&ndash;': '–',
        '&middot;': '·', '&amp;': '&'}


def plain(s):
    for k, v in ENTS.items():
        s = s.replace(k, v)
    return s


DATA = {k: [plain(f), plain(g)] for k, (f, g) in gloss_terms.TERMS.items()}

CSS = """
<style>
/* ---------- abbreviation glossary ---------- */
abbr.gl{
  text-decoration:none;border-bottom:1px dotted var(--accent);
  cursor:help;white-space:nowrap;
}
abbr.gl:hover,abbr.gl:focus-visible{color:var(--accent);border-bottom-style:solid}
figure svg text.gl-svg{cursor:help;text-decoration:underline dotted}
figure svg text.gl-svg:focus-visible{outline:none;font-weight:600}
#gloss{
  position:fixed;left:0;top:0;z-index:80;max-width:288px;
  background:var(--surface);border:1px solid var(--line);
  border-left:3px solid var(--accent);box-shadow:var(--shadow);
  padding:11px 13px;font-size:0.85rem;line-height:1.45;color:var(--ink-soft);
  opacity:0;visibility:hidden;pointer-events:none;transition:opacity .12s ease;
}
#gloss.on{opacity:1;visibility:visible}
#gloss b{
  display:block;color:var(--ink);font-weight:600;margin-bottom:3px;
  font-family:"IBM Plex Sans",sans-serif;font-size:0.88rem;
}
#gloss i{
  display:block;font-style:normal;font-family:"IBM Plex Mono",monospace;
  font-size:0.62rem;letter-spacing:0.1em;text-transform:uppercase;
  color:var(--ink-faint);margin-bottom:6px;
}
</style>
"""

JS = """
<script>
/* Wraps the first mention of each abbreviation in every section, and shows the
   expansion on hover, on focus, or on a tap. Nothing is wrapped inside code
   blocks or diagrams, and each term is marked at most once per section so the
   page does not turn into a field of dotted underlines. */
(function () {
  "use strict";
  var G = __DATA__;

  var keys = Object.keys(G).sort(function (a, b) { return b.length - a.length; });
  var RE;
  try {
    RE = new RegExp("(?<![\\\\w-])(" + keys.join("|") + ")(?![\\\\w-])", "g");
  } catch (e) {
    RE = new RegExp("\\\\b(" + keys.join("|") + ")\\\\b", "g");   /* no lookbehind */
  }
  var SKIP = /^(PRE|CODE|SCRIPT|STYLE|ABBR|TEXTAREA|SVG|BUTTON|A)$/;

  function mark(scope) {
    var seen = Object.create(null), nodes = [], w, n;
    w = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT, null);
    while ((n = w.nextNode())) {
      var skip = false;
      for (var p = n.parentNode; p && p !== scope; p = p.parentNode) {
        if (p.nodeType === 1 && SKIP.test(p.nodeName.toUpperCase())) { skip = true; break; }
      }
      if (!skip && n.nodeValue.length > 1) nodes.push(n);
    }

    nodes.forEach(function (node) {
      var t = node.nodeValue, frag = null, last = 0, m;
      RE.lastIndex = 0;
      while ((m = RE.exec(t))) {
        var k = m[1];
        if (seen[k]) continue;
        seen[k] = 1;
        frag = frag || document.createDocumentFragment();
        if (m.index > last) frag.appendChild(document.createTextNode(t.slice(last, m.index)));
        var a = document.createElement("abbr");
        a.className = "gl";
        a.tabIndex = 0;
        a.setAttribute("data-full", G[k][0]);
        a.setAttribute("data-note", G[k][1]);
        a.textContent = k;
        frag.appendChild(a);
        last = m.index + k.length;
      }
      if (frag) {
        if (last < t.length) frag.appendChild(document.createTextNode(t.slice(last)));
        node.parentNode.replaceChild(frag, node);
      }
    });
  }

  var scopes = document.querySelectorAll(".topic, .part-head, .hero, .footer");
  Array.prototype.forEach.call(scopes, mark);

  /* A diagram label that is exactly one abbreviation gets the same treatment.
     Sub-word wrapping is impossible inside SVG, so only whole labels qualify. */
  Array.prototype.forEach.call(document.querySelectorAll("figure svg text"), function (t) {
    var k = (t.textContent || "").trim();
    if (!G[k] || t.getElementsByTagName("tspan").length) return;
    t.setAttribute("class", (t.getAttribute("class") || "") + " gl-svg");
    t.setAttribute("tabindex", "0");
    t.setAttribute("data-full", G[k][0]);
    t.setAttribute("data-note", G[k][1]);
  });

  /* ---------- the panel ---------- */
  var tip = document.createElement("div");
  tip.id = "gloss";
  tip.setAttribute("role", "tooltip");
  document.body.appendChild(tip);

  var cur = null, pinned = false, showT = 0, hideT = 0;

  function place(el) {
    var r = el.getBoundingClientRect();
    var w = tip.offsetWidth, h = tip.offsetHeight;
    var x = Math.min(Math.max(8, r.left), Math.max(8, window.innerWidth - w - 8));
    var y = r.bottom + 8;
    if (y + h > window.innerHeight - 8) y = Math.max(8, r.top - h - 8);
    tip.style.left = Math.round(x) + "px";
    tip.style.top = Math.round(y) + "px";
  }

  function show(el) {
    if (cur === el && tip.classList.contains("on")) { place(el); return; }
    tip.textContent = "";
    var kicker = document.createElement("i");
    kicker.textContent = (el.textContent || "").trim();
    var full = document.createElement("b");
    full.textContent = el.getAttribute("data-full");
    tip.appendChild(kicker);
    tip.appendChild(full);
    tip.appendChild(document.createTextNode(el.getAttribute("data-note")));
    tip.classList.add("on");
    if (cur) cur.removeAttribute("aria-describedby");
    cur = el;
    el.setAttribute("aria-describedby", "gloss");
    place(el);
  }

  function hide() {
    tip.classList.remove("on");
    if (cur) cur.removeAttribute("aria-describedby");
    cur = null;
    pinned = false;
  }

  function target(e) {
    return e.target && e.target.closest ? e.target.closest("abbr.gl, text.gl-svg") : null;
  }

  document.addEventListener("mouseover", function (e) {
    var el = target(e);
    if (!el || pinned) return;
    clearTimeout(hideT); clearTimeout(showT);
    showT = setTimeout(function () { show(el); }, 60);
  });

  document.addEventListener("mouseout", function (e) {
    if (pinned || !target(e)) return;
    clearTimeout(showT);
    hideT = setTimeout(hide, 140);
  });

  document.addEventListener("click", function (e) {
    var el = target(e);
    if (el) {
      e.preventDefault();
      clearTimeout(showT); clearTimeout(hideT);
      if (pinned && cur === el) { hide(); return; }
      pinned = false;
      show(el);
      pinned = true;                       /* a tap keeps it open until dismissed */
      return;
    }
    if (pinned) hide();
  });

  document.addEventListener("focusin", function (e) {
    var el = target(e);
    if (el) { clearTimeout(hideT); show(el); }
  });

  document.addEventListener("focusout", function (e) {
    if (target(e)) { pinned = false; hide(); }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && cur) hide();
  });

  window.addEventListener("scroll", function () {
    if (!cur) return;
    if (pinned) place(cur); else hide();
  }, { passive: true });

  window.addEventListener("resize", function () { if (cur) place(cur); });
})();
</script>
"""


def inject(path):
    s = open(path, encoding='utf-8').read()
    note = 'injected'
    if MARK in s:                      # replace the old block rather than stack one
        s = s[:s.index(MARK)]
        note = 're-injected'
    block = MARK + '\n' + CSS.strip() + '\n' + JS.strip().replace(
        '__DATA__', json.dumps(DATA, ensure_ascii=False, sort_keys=True)) + '\n'
    out = s.rstrip() + '\n\n' + block
    # Same normalisation the other two passes apply: one blank line before a
    # marker, however many the previous pass happened to leave.
    out = re.sub(r'\n{2,}(?=<!-- /?(?:highlight|print|glossary) -->)', '\n', out)
    open(path, 'w', encoding='utf-8').write(out)
    return '%s, %d terms' % (note, len(DATA))


for page in (sys.argv[1:] or PAGES):
    print('%-28s %s' % (page, inject(page)))
