# -*- coding: utf-8 -*-
"""The colour-theme switch, and the one place its markup and behaviour live.

Every page in the series was already built for three theme states -- the bare
`:root` block is the light palette, `@media (prefers-color-scheme: dark)` guarded
as `:root:not([data-theme="light"])` follows the system, and
`:root[data-theme="dark"]` wins over both. What was missing was anything that
ever set the attribute, so a reader got whatever their operating system said and
had no way to disagree.

Three states, not two. A plain light/dark toggle would throw away the
follow-my-system behaviour the pages already had, which is a regression for
anyone who liked it, so the control is System / Light / Dark and "System" is
what an untouched page uses.

This is a *site* feature, not a page feature. The pages are also published as
artifacts, where the claude.ai host already gives the viewer a theme control and
its frame runtime stamps this very attribute -- two writers for one attribute is
a fight. So the block is spliced in by site_build.mjs, alongside the other
site-only transformations it already does (swapping the font stylesheet for the
self-hosted one, registering the offline cache), and theme_sync.py writes it
into the two hand-written pages site_build does not produce. The artifacts are
left byte-identical. The framing guard below is belt and braces for anyone who
embeds the served site somewhere that manages the theme itself.

The detail that is easiest to get wrong: the choice is applied *synchronously*,
before the topbar is even parsed. Deferring it to DOMContentLoaded paints the
operating system's theme first and then flips, which is the flash every themed
site is judged on.

The icons are inline SVG rather than characters. The site self-hosts only the
latin and greek subsets of its faces, so a sun or a moon glyph would fall back
to whatever the system had -- which is how you get a coloured emoji in the
middle of a monochrome bar, or a blank box.
"""

KEY = 'ladder-theme'
OPEN, CLOSE = '<!-- theme -->', '<!-- /theme -->'

# Drawn at a 24-unit grid and scaled down, so the three read as one set: a
# half-filled disc for "follow the system", a sun, a crescent.
ICONS = {
    'system': ('<circle cx="12" cy="12" r="9"/>'
               '<path d="M12 3a9 9 0 0 0 0 18z" fill="currentColor" stroke="none"/>'),
    'light': ('<circle cx="12" cy="12" r="4.2"/>'
              '<path d="M12 2.4v2.2M12 19.4v2.2M2.4 12h2.2M19.4 12h2.2'
              'M5.2 5.2l1.6 1.6M17.2 17.2l1.6 1.6M18.8 5.2l-1.6 1.6M6.8 17.2l-1.6 1.6"/>'),
    'dark': '<path d="M20.5 14.7A8.6 8.6 0 0 1 9.3 3.5a8.6 8.6 0 1 0 11.2 11.2z"/>',
}

LABELS = [('system', 'Match the system theme'),
          ('light', 'Light theme'),
          ('dark', 'Dark theme')]

CSS = """
<style>
/* ---------- colour theme switch ---------- */
.themebar{display:inline-flex;border:1px solid var(--line);background:var(--surface);
  flex:0 0 auto;align-items:stretch}
.themebar button{display:inline-flex;align-items:center;justify-content:center;
  width:31px;height:26px;padding:0;background:transparent;color:var(--ink-faint);
  border:0;border-right:1px solid var(--line);cursor:pointer;line-height:0}
.themebar button:last-child{border-right:0}
.themebar button:hover{color:var(--ink)}
.themebar button[aria-pressed="true"]{background:var(--accent);color:var(--ground)}
.themebar button:focus-visible{outline:2px solid var(--accent);outline-offset:-3px}
.themebar svg{width:14px;height:14px;display:block;fill:none;stroke:currentColor;
  stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
/* the front page and the 404 have no bar for it to sit in */
.themebar.float{position:fixed;top:14px;right:14px;z-index:60;box-shadow:var(--shadow)}
@media print{.themebar{display:none!important}}

/* Room for it on a phone. The reading progress bar is sixty pixels wide at
   that size and tells nobody anything; two pages already hid it for
   themselves and this generalises that. The bar was over its width budget on
   several pages even before the switch was added. */
@media (max-width:760px){
  .topbar .progress,.topbar .pct{display:none}
  .themebar button{width:27px}
}
/* The bar scrolls sideways when it is over budget, and the first thing to
   scroll out of reach was Contents -- the only navigation a phone has.
   Pinning it to the right edge means whatever else overflows, the way out
   never does. The background matches the bar so nothing shows through
   underneath it. */
.topbar-in .toc-toggle{position:sticky;right:0;
  background:color-mix(in srgb,var(--ground) 88%,var(--surface))}
</style>
"""


def _buttons():
    out = []
    for mode, title in LABELS:
        out.append(
            '<button type="button" data-theme-set="%s" title="%s" aria-label="%s">'
            '<svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></button>'
            % (mode, title, title, ICONS[mode]))
    return ''.join(out)


JS = """
<script>
(function () {
  "use strict";
  var KEY = "%(key)s";
  var root = document.documentElement;

  /* If this page is ever embedded somewhere that manages the theme itself,
     leave the attribute alone and show no control -- two writers is a fight. */
  var framed;
  try { framed = window.top !== window.self; } catch (e) { framed = true; }

  function stored() {
    try {
      var v = localStorage.getItem(KEY);
      return v === "light" || v === "dark" ? v : "system";
    } catch (e) { return "system"; }
  }

  /* The theme-color metas are gated on prefers-color-scheme, so an explicit
     choice has to move them too or the browser's own chrome keeps following
     the operating system while the page does not. */
  function chrome(mode) {
    var metas = document.querySelectorAll('meta[name="theme-color"]');
    if (!metas.length) return;
    for (var i = 0; i < metas.length; i++) {
      var m = metas[i], q = m.getAttribute("data-media") || m.getAttribute("media") || "";
      if (q && !m.getAttribute("data-media")) m.setAttribute("data-media", q);
      if (mode === "system") m.setAttribute("media", m.getAttribute("data-media") || "");
      else {
        var isDark = (m.getAttribute("data-media") || "").indexOf("dark") >= 0;
        m.setAttribute("media", (isDark === (mode === "dark")) ? "all" : "not all");
      }
    }
  }

  function apply(mode) {
    if (mode === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", mode);
    chrome(mode);
  }

  /* Synchronously, before the page below this block is parsed: deferring it
     paints the system theme first and then flips. */
  if (!framed) apply(stored());

  function mount() {
    if (framed) return;
    var bar = document.createElement("div");
    bar.className = "themebar";
    bar.setAttribute("role", "group");
    bar.setAttribute("aria-label", "Colour theme");
    bar.innerHTML = %(buttons)s;

    var btns = bar.querySelectorAll("button");
    function paint(mode) {
      for (var i = 0; i < btns.length; i++) {
        btns[i].setAttribute("aria-pressed",
          btns[i].getAttribute("data-theme-set") === mode ? "true" : "false");
      }
    }
    for (var i = 0; i < btns.length; i++) {
      btns[i].addEventListener("click", function () {
        var mode = this.getAttribute("data-theme-set");
        apply(mode);
        paint(mode);
        try {
          if (mode === "system") localStorage.removeItem(KEY);
          else localStorage.setItem(KEY, mode);
        } catch (e) {}
      });
    }
    paint(stored());

    /* In the bar where there is one, top right where there is not -- the
       front page and the 404 have no topbar.

       Ahead of the language switch rather than after it. On a phone the bar
       is over budget on the two pages that carry both, and whatever sits
       last is what scrolls out of sight; the theme applies to every page and
       is the one a reader goes looking for, while the language switch is
       page-specific and is also named under every snippet and bound to a
       key. So the language switch is the one that scrolls. */
    var slot = document.querySelector(".topbar-in");
    var before = document.querySelector(".topbar-in .langbar") ||
                 document.getElementById("toc-toggle");
    if (slot && before) slot.insertBefore(bar, before);
    else if (slot) slot.appendChild(bar);
    else { bar.className += " float"; document.body.appendChild(bar); }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else { mount(); }
})();
</script>
"""


def block():
    """The whole switch -- styles, the pre-paint application, and the control."""
    body = JS % {'key': KEY, 'buttons': _json(_buttons())}
    return '\n'.join([OPEN, CSS.strip(), body.strip(), CLOSE, ''])


def _json(s):
    import json
    return json.dumps(s)
