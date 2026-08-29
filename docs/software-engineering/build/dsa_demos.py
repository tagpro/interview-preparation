# -*- coding: utf-8 -*-
"""The interactive figures on the algorithms page.

One small player and eleven demos, in plain JavaScript with no dependencies, so
the page keeps the series' promise: nothing is fetched at runtime and the whole
thing works off a memory stick.

Every demo is a *trace*: the algorithm is run once, up front, and each
interesting moment is recorded as a frame. Frames are cheap here -- these run on
a few dozen items -- and precomputing them buys two things a coroutine cannot.
The reader can step backwards, and the figure's initial state is deterministic,
which is what lets the print pass render the same ink twice.

Nothing autoplays. A figure that started moving on its own would be noise while
you are reading the paragraph above it, and it would make the printed page
depend on when Chrome happened to take the snapshot.

Everything is drawn as DOM or SVG, never a canvas, so it prints.
"""

P1 = r"""
<script>
(function () {
  "use strict";

  /* ==================================================================
     The player
     ================================================================== */

  var REG = {};
  function reg(name, factory) { REG[name] = factory; }

  function el(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt != null) e.textContent = txt;
    return e;
  }
  function btn(label, title) {
    var b = el("button", null, label);
    b.type = "button";
    if (title) b.title = title;
    return b;
  }
  function sel(options, value) {
    var s = document.createElement("select");
    options.forEach(function (o) {
      var op = document.createElement("option");
      op.value = o[0]; op.textContent = o[1];
      if (o[0] === value) op.selected = true;
      s.appendChild(op);
    });
    return s;
  }
  function commas(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ","); }

  var REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function mount(fig) {
    var factory = REG[fig.getAttribute("data-demo")];
    if (!factory) return;
    var stage = fig.querySelector(".demo-stage");
    var read = fig.querySelector(".demo-read");
    var ctl = fig.querySelector(".demo-ctl");
    if (!stage || !ctl) return;
    ctl.innerHTML = "";
    stage.innerHTML = "";

    var frames = null, at = 0, timer = 0, playing = false, demo;
    var play, prev, next;

    var api = {
      fig: fig, stage: stage, read: read, ctl: ctl,
      speed: 130,
      /* readout line under the stage */
      say: function (html) { if (read) read.innerHTML = html; },
      /* recompute the trace after a control changed */
      rebuild: function (keepAt) {
        stop();
        frames = demo.frames ? demo.frames() : null;
        at = !frames ? 0
           : keepAt ? Math.min(at, frames.length - 1)
           : demo.start ? Math.min(Math.max(0, demo.start(frames)), frames.length - 1)
           : 0;
        paint();
      },
      at: function () { return at; },
      total: function () { return frames ? frames.length : 0; },
      /* controls the demo owns, added left of the transport */
      add: function (node) { ctl.appendChild(node); return node; },
      button: btn, select: sel, el: el, commas: commas
    };

    demo = factory(api);

    if (demo.frames) {
      var seg = el("div", "seg nav");
      prev = btn("◀", "Step back (left arrow)");
      play = btn("Play", "Play or pause (space)");
      next = btn("▶", "Step forward (right arrow)");
      seg.appendChild(prev); seg.appendChild(play); seg.appendChild(next);
      ctl.appendChild(seg);
      var reset = btn("Reset");
      ctl.appendChild(reset);

      prev.addEventListener("click", function () { stop(); go(at - 1); });
      next.addEventListener("click", function () { stop(); go(at + 1); });
      reset.addEventListener("click", function () { stop(); go(0); });
      play.addEventListener("click", function () { playing ? stop() : start(); });

      fig.addEventListener("keydown", function (e) {
        var tag = (e.target.tagName || "").toLowerCase();
        if (tag === "input" || tag === "select" || tag === "textarea") return;
        if (e.key === "ArrowRight") { stop(); go(at + 1); e.preventDefault(); }
        else if (e.key === "ArrowLeft") { stop(); go(at - 1); e.preventDefault(); }
        else if (e.key === " " || e.key === "Spacebar") {
          if (e.target.tagName === "BUTTON") return;   /* let the button take it */
          playing ? stop() : start(); e.preventDefault();
        }
      });
    }

    function go(i) {
      if (!frames || !frames.length) return;
      at = Math.max(0, Math.min(frames.length - 1, i));
      paint();
    }
    function paint() {
      if (frames) {
        demo.render(frames[at], at, frames.length);
        if (prev) prev.disabled = at === 0;
        if (next) next.disabled = at === frames.length - 1;
      } else {
        demo.render();
      }
    }
    function start() {
      if (!frames) return;
      if (at >= frames.length - 1) at = 0;
      playing = true; play.textContent = "Pause"; play.setAttribute("aria-pressed", "true");
      timer = setInterval(function () {
        if (at >= frames.length - 1) { stop(); return; }
        go(at + 1);
      }, REDUCED ? Math.max(api.speed, 320) : api.speed);
    }
    function stop() {
      playing = false;
      if (play) { play.textContent = "Play"; play.setAttribute("aria-pressed", "false"); }
      clearInterval(timer); timer = 0;
    }

    api.rebuild();
  }

  /* ==================================================================
     1. How fast the cost grows
     ================================================================== */

  function sci(x) {
    if (!isFinite(x)) return "beyond counting";
    if (x < 1e6) return commas(x);
    var e = Math.floor(Math.log(x) / Math.LN10), m = x / Math.pow(10, e);
    return (Math.round(m * 10) / 10) + " &times; 10<sup>" + e + "</sup>";
  }
  function dur(s) {
    if (!isFinite(s) || s > 3.15e26) return "longer than the universe";
    if (s < 1e-6) return (s * 1e9).toFixed(0) + " ns";
    if (s < 1e-3) return (s * 1e6).toFixed(1) + " &micro;s";
    if (s < 1) return (s * 1e3).toFixed(1) + " ms";
    if (s < 90) return s.toFixed(1) + " s";
    if (s < 5400) return (s / 60).toFixed(1) + " min";
    if (s < 1.3e5) return (s / 3600).toFixed(1) + " hours";
    if (s < 3.1e7) return (s / 86400).toFixed(0) + " days";
    if (s < 3.1e11) return (s / 3.156e7).toFixed(0) + " years";
    return sci(s / 3.156e7) + " years";
  }

  reg("growth", function (api) {
    /* One billion simple operations a second is the right order of magnitude for
       a single core, and it makes the arithmetic reader-checkable. */
    var RATE = 1e9;
    var FN = [
      ["O(1)", function () { return 1; }, "fine"],
      ["O(log n)", function (n) { return Math.log(n) / Math.LN2; }, "fine"],
      ["O(n)", function (n) { return n; }, ""],
      ["O(n log n)", function (n) { return n * Math.log(n) / Math.LN2; }, ""],
      ["O(n<sup>2</sup>)", function (n) { return n * n; }, "hot"],
      ["O(2<sup>n</sup>)", function (n) { return Math.pow(2, n); }, "hot"],  /* the wall */
      ["O(n!)", function (n) { var r = 1; for (var i = 2; i <= Math.min(n, 200); i++) r *= i; return n > 200 ? Infinity : r; }, "hot"]
    ];

    var wrap = el("div", "growth");
    var left = el("div"), right = el("div");
    wrap.appendChild(left); wrap.appendChild(right);
    api.stage.appendChild(wrap);

    var range = document.createElement("input");
    range.type = "range"; range.min = "0"; range.max = "100"; range.value = "46";
    range.setAttribute("aria-label", "Input size");
    var label = el("p", "nojs");
    left.appendChild(label); left.appendChild(range);
    var plot = el("div"); left.appendChild(plot);
    var table = el("table", "gtab"); right.appendChild(table);

    function n() { return Math.max(2, Math.round(Math.pow(10, 0.3 + range.value / 100 * 6.7))); }

    function drawPlot(cur) {
      /* log-log, so every one of these is a straight-ish line and the only thing
         that separates them is slope -- which is the whole point. */
      var W = 300, H = 150, x0 = 26, y0 = 128, x1 = 296, y1 = 8;
      var LX = 7, LY = 24;                       /* decades on each axis */
      var px = function (lx) { return x0 + lx / LX * (x1 - x0); };
      var py = function (ly) { return y0 - Math.min(ly, LY) / LY * (y0 - y1); };
      var paths = FN.map(function (f, i) {
        var pts = [];
        for (var k = 0; k <= 40; k++) {
          var lx = k / 40 * LX, v = f[1](Math.pow(10, lx));
          var ly = v > 0 ? Math.log(v) / Math.LN10 : 0;
          if (!isFinite(ly)) ly = LY + 1;
          pts.push(px(lx).toFixed(1) + "," + py(ly).toFixed(1));
          if (ly > LY) break;
        }
        var cls = f[2] === "hot" ? "svg-l3" : f[2] === "fine" ? "svg-l1" : "svg-l2";
        return '<polyline class="' + cls + '" points="' + pts.join(" ") +
               '" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.9"/>';
      });
      var mx = px(Math.log(cur) / Math.LN10);
      api._plotSvg =
        '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Operation count against input size, both axes logarithmic">' +
        '<line x1="' + x0 + '" y1="' + y0 + '" x2="' + x1 + '" y2="' + y0 + '" stroke="currentColor" stroke-width="1" opacity="0.35"/>' +
        '<line x1="' + x0 + '" y1="' + y0 + '" x2="' + x0 + '" y2="' + y1 + '" stroke="currentColor" stroke-width="1" opacity="0.35"/>' +
        '<line x1="' + mx.toFixed(1) + '" y1="' + y1 + '" x2="' + mx.toFixed(1) + '" y2="' + y0 + '" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3" opacity="0.55"/>' +
        paths.join("") +
        '<text x="' + x0 + '" y="146" font-size="9" opacity="0.6">n = 1</text>' +
        '<text x="' + (x1 - 42) + '" y="146" font-size="9" opacity="0.6">n = 10 M</text>' +
        [0, 8, 16, 24].map(function (ly) {
          return '<text x="2" y="' + (py(ly) + 3).toFixed(1) + '" font-size="8" opacity="0.45">10' +
                 '<tspan font-size="6" dy="-3">' + ly + '</tspan></text>';
        }).join("") +
        "</svg>";
      plot.innerHTML = api._plotSvg;
    }

    function render() {
      var N = n();
      label.innerHTML = "n = <b>" + commas(N) + "</b>";
      var rows = ['<tr><th>growth</th><th>operations</th><th>at 10<sup>9</sup>/s</th></tr>'];
      FN.forEach(function (f) {
        var v = f[1](N);
        rows.push('<tr class="' + f[2] + '"><td>' + f[0] + "</td><td>" + sci(v) +
                  "</td><td>" + dur(v / RATE) + "</td></tr>");
      });
      table.innerHTML = rows.join("");
      drawPlot(N);
      api.say('Everything below <b>O(n log n)</b> is a rounding error at this size. ' +
              'The line that matters is where <b>O(n<sup>2</sup>)</b> stops being ' +
              'instant &mdash; drag until its column turns orange.');
    }

    range.addEventListener("input", render);
    return { render: render };
  });

  /* ==================================================================
     2. How a dynamic array grows
     ================================================================== */

  reg("array", function (api) {
    var STRATS = [
      ["2", "double the capacity"],
      ["1.5", "grow by half (Java ArrayList)"],
      ["1.125", "grow by an eighth (CPython, roughly)"],
      ["1.0", "grow by exactly one"]
    ];
    var pick = api.add(sel(STRATS, "2"));
    pick.setAttribute("aria-label", "Growth strategy");
    pick.addEventListener("change", function () { api.rebuild(); });

    var cells = el("div", "cells"), idx = el("div", "idx");
    api.stage.appendChild(cells); api.stage.appendChild(idx);

    return {
      start: function (F) { return Math.min(16, F.length - 1); },
      frames: function () {
        var f = Math.max(1.0, parseFloat(pick.value));
        var len = 0, cap = 0, copies = 0, F = [], grows = 0;
        for (var i = 0; i < 40; i++) {
          var grew = false;
          if (len === cap) {
            var want = cap === 0 ? 1 : Math.max(cap + 1, Math.floor(cap * f));
            copies += len; cap = want; grew = true; grows++;
          }
          len++;
          F.push({ len: len, cap: cap, copies: copies, grew: grew, grows: grows });
        }
        return F;
      },
      render: function (s, i, n) {
        var out = [], ix = [];
        for (var k = 0; k < Math.max(s.cap, 1); k++) {
          out.push('<span class="cell ' + (k < s.len ? (s.grew ? "warn" : "hit") : "empty") + '">' +
                   (k < s.len ? k : "&middot;") + "</span>");
          ix.push("<span>" + (k % 5 === 0 ? k : "") + "</span>");
        }
        cells.innerHTML = out.join(""); idx.innerHTML = ix.join("");
        var avg = s.copies / s.len;
        api.say("append #<span class='n'>" + s.len + "</span> &nbsp; len <span class='n'>" + s.len +
                "</span> &nbsp; cap <span class='n'>" + s.cap + "</span> &nbsp; reallocations <span class='n'>" +
                s.grows + "</span> &nbsp; elements copied so far <span class='n'>" + commas(s.copies) +
                "</span> &nbsp;&middot;&nbsp; <b>" + (Math.round(avg * 100) / 100) +
                " copies per append</b>" + (s.grew ? " &nbsp;&larr; this one reallocated" : ""));
      }
    };
  });

  /* ==================================================================
     3. A hash table, and what a bad hash does to it
     ================================================================== */

  reg("hash", function (api) {
    var WORDS = ["ash", "birch", "cedar", "elm", "fir", "hazel", "larch", "maple",
                 "oak", "pine", "rowan", "spruce", "willow", "yew", "alder", "beech"];
    var pick = api.add(sel([["good", "a hash that mixes"], ["bad", "hash = length of key"]], "good"));
    pick.setAttribute("aria-label", "Hash function");
    pick.addEventListener("change", function () { api.rebuild(); });

    var rows = el("div", "rows tight");
    api.stage.appendChild(rows);

    function h(word, mode) {
      if (mode === "bad") return word.length;
      var x = 2166136261;                       /* FNV-1a, 32-bit */
      for (var i = 0; i < word.length; i++) {
        x ^= word.charCodeAt(i);
        x = (x * 16777619) >>> 0;
      }
      return x >>> 0;
    }

    return {
      start: function (F) { return Math.min(7, F.length - 1); },
      frames: function () {
        var mode = pick.value, nb = 8, buckets = [], F = [], i;
        for (i = 0; i < nb; i++) buckets.push([]);
        var count = 0;
        function snap(extra) {
          F.push(Object.assign({ b: buckets.map(function (x) { return x.slice(); }), nb: nb, count: count }, extra));
        }
        snap({ note: "empty table, " + nb + " buckets" });
        for (i = 0; i < WORDS.length; i++) {
          var w = WORDS[i], hv = h(w, mode), at = hv % nb;
          buckets[at].push(w); count++;
          snap({ key: w, hv: hv, at: at, note: "insert" });
          if (count / nb > 0.75) {
            var old = buckets;
            nb *= 2; buckets = [];
            for (var k = 0; k < nb; k++) buckets.push([]);
            old.forEach(function (chain) {
              chain.forEach(function (x) { buckets[h(x, mode) % nb].push(x); });
            });
            snap({ note: "resize", at: -1 });
          }
        }
        return F;
      },
      render: function (s) {
        var out = [];
        for (var i = 0; i < s.nb; i++) {
          var cs = s.b[i].map(function (w, j) {
            var hot = s.key === w && s.at === i;
            return '<span class="cell ' + (hot ? "warn" : "hit") + '">' + w + "</span>";
          });
          if (!cs.length) cs = ['<span class="cell empty">&middot;</span>'];
          out.push('<div class="row"><span class="lab">' + i + "</span>" +
                   '<span class="cells">' + cs.join("") + "</span></div>");
        }
        rows.innerHTML = out.join("");
        var longest = 0;
        s.b.forEach(function (c) { longest = Math.max(longest, c.length); });
        var load = (s.count / s.nb).toFixed(2);
        if (s.note === "resize") {
          api.say("<b>Load factor passed 0.75 &mdash; the table doubled to " + s.nb +
                  " buckets and rehashed every key.</b> That one insert cost O(n). " +
                  "Spread over all the cheap ones, appends are still O(1) amortised.");
        } else if (s.key) {
          api.say("h(<b>" + s.key + "</b>) = <span class='n'>" + s.hv + "</span> &nbsp; " +
                  s.hv + " mod " + s.nb + " = bucket <span class='n'>" + s.at + "</span> &nbsp;&middot;&nbsp; " +
                  "load factor <span class='n'>" + load + "</span> &nbsp; longest chain <span class='n'>" +
                  longest + "</span>" +
                  (longest > 3 ? " &nbsp;&larr; <b>this is no longer a hash table, it is a linked list</b>" : ""));
        } else {
          api.say("Sixteen tree names into eight buckets. Watch the longest chain: it is " +
                  "the real cost of a lookup, and the average tells you nothing about it.");
        }
      }
    };
  });
"""

P2 = r"""
  /* ==================================================================
     4. Five sorts, side by side, with the counters showing
     ================================================================== */

  reg("sort", function (api) {
    var N = 30;
    var algo = api.add(sel([
      ["insertion", "insertion sort"], ["selection", "selection sort"],
      ["bubble", "bubble sort"], ["merge", "merge sort"],
      ["quick", "quicksort"], ["heap", "heapsort"]
    ], "quick"));
    algo.setAttribute("aria-label", "Algorithm");
    var shape = api.add(sel([
      ["shuffled", "shuffled"], ["sorted", "already sorted"],
      ["reversed", "reversed"], ["few", "few distinct values"]
    ], "shuffled"));
    shape.setAttribute("aria-label", "Input order");
    var again = api.add(api.button("Reshuffle"));
    algo.addEventListener("change", function () { api.rebuild(); });
    shape.addEventListener("change", function () { seed(); api.rebuild(); });
    again.addEventListener("click", function () { seed(); api.rebuild(); });

    var bars = el("div", "bars");
    api.stage.appendChild(bars);
    api.stage.appendChild(legend([["--ink-faint", "untouched"], ["--l2", "compared"],
                                  ["--l3", "moved / pivot"], ["--l1", "in final place"]]));
    api.speed = 70;

    var data = [];
    function seed() {
      var i;
      data = [];
      if (shape.value === "few") { for (i = 0; i < N; i++) data.push(1 + Math.floor(Math.random() * 4) * 8); }
      else { for (i = 0; i < N; i++) data.push(i + 1); }
      if (shape.value === "shuffled" || shape.value === "few") {
        for (i = N - 1; i > 0; i--) {
          var j = Math.floor(Math.random() * (i + 1)), t = data[i]; data[i] = data[j]; data[j] = t;
        }
      } else if (shape.value === "reversed") data.reverse();
    }
    seed();

    function trace() {
      var a = data.slice(), F = [], c = 0, m = 0, n = a.length, fin = {};
      function push(o) {
        o = o || {}; o.a = a.slice(); o.c = c; o.m = m;
        o.fin = Object.keys(fin); F.push(o); return o;
      }
      function swap(i, j) { var t = a[i]; a[i] = a[j]; a[j] = t; m += 2; }

      if (algo.value === "insertion") {
        push({ pre: 1, note: "one element is a sorted list" });
        for (var i = 1; i < n; i++) {
          var key = a[i], j = i - 1;
          push({ cmp: [i], pre: i, note: "lift a[" + i + "] out and walk it left" });
          while (j >= 0) {
            c++;
            if (a[j] <= key) break;
            a[j + 1] = a[j]; m++; j--;
            push({ cmp: [j + 1], mv: [j + 2], pre: i, note: "bigger &mdash; shift it right" });
          }
          a[j + 1] = key; m++;
          push({ mv: [j + 1], pre: i + 1, note: "drop it in at " + (j + 1) });
        }
      } else if (algo.value === "selection") {
        for (var s = 0; s < n - 1; s++) {
          var min = s;
          for (var k = s + 1; k < n; k++) {
            c++;
            push({ cmp: [k, min], pre: s, note: "scanning for the smallest from " + s });
            if (a[k] < a[min]) min = k;
          }
          if (min !== s) swap(s, min);
          push({ mv: [s, min], pre: s + 1, note: "smallest goes to " + s });
        }
        push({ pre: n });
      } else if (algo.value === "bubble") {
        var end = n, moved = true;
        while (moved && end > 1) {
          moved = false;
          for (var b = 0; b + 1 < end; b++) {
            c++;
            push({ cmp: [b, b + 1], suf: end, note: "compare neighbours" });
            if (a[b] > a[b + 1]) { swap(b, b + 1); moved = true; push({ mv: [b, b + 1], suf: end, note: "out of order &mdash; swap" }); }
          }
          end--;
        }
        push({ pre: n, note: "no swaps in a whole pass &mdash; done" });
      } else if (algo.value === "merge") {
        var buf = a.slice();
        for (var w = 1; w < n; w *= 2) {
          for (var lo = 0; lo < n; lo += 2 * w) {
            var mid = Math.min(lo + w, n), hi = Math.min(lo + 2 * w, n);
            if (mid >= hi) continue;
            var p = lo, q = mid, o = lo;
            push({ dim: [lo, hi - 1], note: "merge two runs of " + w });
            while (p < mid && q < hi) {
              c++;
              push({ dim: [lo, hi - 1], cmp: [p, q], note: "which head is smaller?" });
              buf[o++] = a[p] <= a[q] ? a[p++] : a[q++];
            }
            while (p < mid) buf[o++] = a[p++];
            while (q < hi) buf[o++] = a[q++];
            for (var t2 = lo; t2 < hi; t2++) { a[t2] = buf[t2]; m++; }
            push({ dim: [lo, hi - 1], mv: rangeArr(lo, hi), note: "the merged run is written back" });
          }
        }
        push({ pre: n, note: "runs of " + n + " &mdash; done" });
      } else if (algo.value === "quick") {
        var stack = [[0, n - 1]];
        while (stack.length) {
          var fr = stack.pop(), l = fr[0], r = fr[1];
          if (l >= r) continue;
          var pv = a[r], i2 = l;
          push({ dim: [l, r], piv: r, note: "pivot is the last element of [" + l + ".." + r + "]" });
          for (var jj = l; jj < r; jj++) {
            c++;
            push({ dim: [l, r], piv: r, cmp: [jj], note: "smaller than the pivot?" });
            if (a[jj] < pv) {
              if (i2 !== jj) swap(i2, jj);
              push({ dim: [l, r], piv: r, mv: [i2, jj], note: "yes &mdash; move it to the left side" });
              i2++;
            }
          }
          swap(i2, r);
          fin[i2] = 1;
          push({ dim: [l, r], mv: [i2, r], note: "pivot lands at " + i2 + " &mdash; it is now final" });
          stack.push([l, i2 - 1]); stack.push([i2 + 1, r]);
        }
        push({ pre: n, note: "every pivot is in place, so the array is" });
      } else {                                     /* heapsort */
        var size = n;
        function sift(i, lim) {
          for (;;) {
            var big = i, L = 2 * i + 1, R = 2 * i + 2;
            if (L < lim) { c++; if (a[L] > a[big]) big = L; }
            if (R < lim) { c++; if (a[R] > a[big]) big = R; }
            push({ cmp: [i, big], suf: size, note: "is a[" + i + "] bigger than both children?" });
            if (big === i) return;
            swap(i, big);
            push({ mv: [i, big], suf: size, note: "no &mdash; sink it" });
            i = big;
          }
        }
        for (var h = Math.floor(n / 2) - 1; h >= 0; h--) sift(h, n);
        push({ suf: size, note: "the array is now a max-heap: every parent beats its children" });
        for (var e = n - 1; e > 0; e--) {
          swap(0, e); size = e;
          push({ mv: [0, e], suf: size, note: "the largest swaps to the end and leaves the heap" });
          sift(0, e);
        }
        push({ pre: n, note: "done" });
      }
      push({ pre: n, note: "sorted" });
      return F;
    }
    function rangeArr(lo, hi) { var o = []; for (var i = lo; i < hi; i++) o.push(i); return o; }

    return {
      frames: trace,
      render: function (f, i, total) {
        var max = 0, k;
        for (k = 0; k < f.a.length; k++) max = Math.max(max, f.a[k]);
        var out = [];
        for (k = 0; k < f.a.length; k++) {
          var cls = "bar";
          if (f.dim && (k < f.dim[0] || k > f.dim[1])) cls += " dim";
          if (k < (f.pre || 0) || (f.suf != null && k >= f.suf) ||
              (f.fin && f.fin.indexOf(String(k)) >= 0)) cls += " ok";
          if (f.piv === k) cls += " piv";
          else if (f.mv && f.mv.indexOf(k) >= 0) cls += " mv";
          else if (f.cmp && f.cmp.indexOf(k) >= 0) cls += " cmp";
          out.push('<span class="' + cls + '" style="height:' + (f.a[k] / max * 100).toFixed(1) + '%"></span>');
        }
        bars.innerHTML = out.join("");
        var nlogn = Math.round(N * Math.log(N) / Math.LN2), sq = Math.round(N * N / 2);
        api.say((f.note ? "<b>" + f.note + "</b> &nbsp;&middot;&nbsp; " : "") +
                "comparisons <span class='n'>" + f.c + "</span> &nbsp; element moves <span class='n'>" +
                f.m + "</span> &nbsp;&middot;&nbsp; for n = " + N + ", n log&#8322;n is about " + nlogn +
                " and n&#178;/2 is about " + commas(sq) + " &nbsp;&middot;&nbsp; step " + (i + 1) + " of " + total);
      }
    };
  });

  function legend(items) {
    var d = el("div", "demo-legend");
    d.innerHTML = items.map(function (it) {
      return '<span><i style="--k:var(' + it[0] + ')"></i>' + it[1] + "</span>";
    }).join("");
    return d;
  }

  /* ==================================================================
     5. Binary search, and the two bounds people actually need
     ================================================================== */

  reg("bsearch", function (api) {
    var A = [2, 3, 3, 5, 8, 8, 8, 8, 11, 13, 14, 14, 17, 21, 23, 23, 29, 31, 37, 41];
    var mode = api.add(sel([
      ["find", "find the value"], ["lower", "lower bound (first &ge;)"], ["upper", "upper bound (first &gt;)"]
    ], "find"));
    mode.setAttribute("aria-label", "Which search");
    var wrap = el("label"); wrap.appendChild(document.createTextNode("target"));
    var tin = document.createElement("input");
    tin.type = "text"; tin.value = "8"; tin.style.width = "4ch";
    wrap.appendChild(tin); api.add(wrap);
    mode.addEventListener("change", function () { api.rebuild(); });
    tin.addEventListener("input", function () { api.rebuild(); });

    var ptr = el("div", "ptr"), cells = el("div", "cells"), idx = el("div", "idx");
    api.stage.appendChild(ptr); api.stage.appendChild(cells); api.stage.appendChild(idx);
    api.speed = 620;

    return {
      frames: function () {
        var t = parseInt(tin.value, 10); if (isNaN(t)) t = 8;
        var F = [], lo = 0, hi = A.length, steps = 0;
        if (mode.value === "find") {
          hi = A.length - 1;
          while (lo <= hi) {
            var mid = (lo + hi) >> 1; steps++;
            F.push({ lo: lo, hi: hi, mid: mid, t: t, steps: steps,
                     note: "a[" + mid + "] = " + A[mid] + (A[mid] === t ? " &mdash; found it" : A[mid] < t ? " &lt; " + t + ", go right" : " &gt; " + t + ", go left") });
            if (A[mid] === t) { F.push({ lo: mid, hi: mid, mid: mid, t: t, steps: steps, done: mid, note: "found at index " + mid }); return F; }
            if (A[mid] < t) lo = mid + 1; else hi = mid - 1;
          }
          F.push({ lo: lo, hi: hi, t: t, steps: steps, done: -1, note: "lo passed hi &mdash; " + t + " is not in the array. lo = " + lo + " is where it would go." });
        } else {
          var wantGreater = mode.value === "upper";
          while (lo < hi) {
            var m2 = (lo + hi) >> 1; steps++;
            var goRight = wantGreater ? A[m2] <= t : A[m2] < t;
            F.push({ lo: lo, hi: hi, mid: m2, t: t, steps: steps, half: true,
                     note: "a[" + m2 + "] = " + A[m2] + (goRight ? " is still too small &mdash; the answer is after it" : " already qualifies &mdash; the answer is at or before it") });
            if (goRight) lo = m2 + 1; else hi = m2;
          }
          F.push({ lo: lo, hi: lo, t: t, steps: steps, done: lo, half: true,
                   note: "lo met hi at " + lo + (mode.value === "lower" ? " &mdash; the first index whose value is &ge; " + t : " &mdash; the first index whose value is &gt; " + t) });
        }
        return F;
      },
      render: function (f, i, total) {
        var top = [], cs = [], ix = [];
        for (var k = 0; k < A.length; k++) {
          var cls = "cell";
          var hiEnd = f.half ? f.hi - 1 : f.hi;
          if (k < f.lo || k > hiEnd) cls += " out";
          if (k === f.mid) cls += " on";
          if (f.done === k) cls += " hit";
          cs.push('<span class="' + cls + '">' + A[k] + "</span>");
          var tag = "";
          if (k === f.lo) tag += "lo";
          if (k === f.hi && f.half) tag += (tag ? "/" : "") + "hi";
          if (!f.half && k === f.hi) tag += (tag ? "/" : "") + "hi";
          if (k === f.mid) tag += (tag ? "/" : "") + "mid";
          top.push('<span style="color:var(--' + (tag.indexOf("mid") >= 0 ? "l2" : "ink-faint") + ')">' + tag + "</span>");
          ix.push("<span>" + k + "</span>");
        }
        ptr.innerHTML = top.join(""); cells.innerHTML = cs.join(""); idx.innerHTML = ix.join("");
        api.say("looking for <b>" + f.t + "</b> &nbsp;&middot;&nbsp; " + f.note +
                " &nbsp;&middot;&nbsp; probes so far <span class='n'>" + f.steps +
                "</span> of at most " + Math.ceil(Math.log(A.length + 1) / Math.LN2) +
                " for " + A.length + " elements");
      }
    };
  });

  /* ==================================================================
     6. A binary heap: the tree that is really an array
     ================================================================== */

  reg("heap", function (api) {
    var seq = [23, 9, 41, 4, 17, 30, 2, 12, 7, 36];
    var pops = 4;
    var more = api.add(api.button("Push a value"));
    var popb = api.add(api.button("Pop the minimum"));
    more.addEventListener("click", function () { seq.push(1 + Math.floor(Math.random() * 48)); api.rebuild(); });
    popb.addEventListener("click", function () { pops++; api.rebuild(); });

    var svg = el("div"), arr = el("div", "cells"), idx = el("div", "idx");
    api.stage.appendChild(svg); api.stage.appendChild(arr); api.stage.appendChild(idx);
    api.speed = 320;

    return {
      // open on the built heap; Reset still winds back to the empty one
      start: function (F) {
        for (var i = F.length - 1; i >= 0; i--)
          if (F[i].note && F[i].note.indexOf("heap property restored") === 0) return i;
        return 0;
      },
      frames: function () {
        var h = [], F = [], cmp = 0;
        function snap(o) { o = o || {}; o.h = h.slice(); o.cmp = cmp; F.push(o); }
        snap({ note: "an empty heap" });
        seq.forEach(function (v) {
          h.push(v);
          var i = h.length - 1;
          snap({ hot: [i], note: "push " + v + " at the end &mdash; the only spot that keeps the tree complete" });
          while (i > 0) {
            var p = (i - 1) >> 1; cmp++;
            snap({ hot: [i], on: [p], note: "is " + h[i] + " smaller than its parent " + h[p] + "?" });
            if (h[p] <= h[i]) break;
            var t = h[p]; h[p] = h[i]; h[i] = t;
            snap({ hot: [p], on: [i], note: "yes &mdash; swim it up" });
            i = p;
          }
          snap({ note: "heap property restored after " + Math.ceil(Math.log(h.length + 1) / Math.LN2) + " levels at most" });
        });
        for (var k = 0; k < pops; k++) {
          if (!h.length) break;
          var top = h[0];
          snap({ hot: [0], note: "the minimum is always at the root: " + top });
          h[0] = h[h.length - 1]; h.pop();
          snap({ hot: [0], note: "the last element takes its place, then sinks" });
          var i2 = 0;
          for (;;) {
            var L = 2 * i2 + 1, R = 2 * i2 + 2, sm = i2;
            if (L < h.length) { cmp++; if (h[L] < h[sm]) sm = L; }
            if (R < h.length) { cmp++; if (h[R] < h[sm]) sm = R; }
            if (sm === i2) break;
            snap({ hot: [i2], on: [sm], note: "child " + h[sm] + " is smaller &mdash; swap" });
            var t2 = h[sm]; h[sm] = h[i2]; h[i2] = t2;
            i2 = sm;
          }
          snap({ note: "popped " + top + "; the heap is " + h.length + " deep-balanced elements again" });
        }
        return F;
      },
      render: function (f) {
        var h = f.h, n = h.length;
        var W = 660, levels = n ? Math.floor(Math.log(n) / Math.LN2) + 1 : 1;
        var H = 30 + levels * 46;
        var parts = [], k;
        function pos(i) {
          var d = Math.floor(Math.log(i + 1) / Math.LN2);
          var first = Math.pow(2, d) - 1, span = Math.pow(2, d);
          return { x: (i - first + 0.5) / span * W, y: 22 + d * 46 };
        }
        for (k = 1; k < n; k++) {
          var a = pos(k), b = pos((k - 1) >> 1);
          parts.push('<line class="edge" x1="' + b.x.toFixed(1) + '" y1="' + (b.y + 13) +
                     '" x2="' + a.x.toFixed(1) + '" y2="' + (a.y - 13) + '"/>');
        }
        for (k = 0; k < n; k++) {
          var p = pos(k);
          var cls = "node";
          if (f.hot && f.hot.indexOf(k) >= 0) cls += " hot";
          else if (f.on && f.on.indexOf(k) >= 0) cls += " on";
          parts.push('<g class="' + cls + '"><circle cx="' + p.x.toFixed(1) + '" cy="' + p.y +
                     '" r="14"/><text x="' + p.x.toFixed(1) + '" y="' + (p.y + 4) +
                     '" text-anchor="middle">' + h[k] + "</text></g>");
        }
        svg.innerHTML = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="The heap drawn as a complete binary tree">' + parts.join("") + "</svg>";
        var cs = [], ix = [];
        for (k = 0; k < n; k++) {
          var c2 = "cell";
          if (f.hot && f.hot.indexOf(k) >= 0) c2 += " warn";
          else if (f.on && f.on.indexOf(k) >= 0) c2 += " on";
          cs.push('<span class="' + c2 + '">' + h[k] + "</span>");
          ix.push("<span>" + k + "</span>");
        }
        arr.innerHTML = cs.join(""); idx.innerHTML = ix.join("");
        api.say((f.note ? "<b>" + f.note + "</b>" : "") +
                " &nbsp;&middot;&nbsp; size <span class='n'>" + n +
                "</span> &nbsp; comparisons <span class='n'>" + f.cmp +
                "</span> &nbsp;&middot;&nbsp; children of i are 2i+1 and 2i+2; there are no pointers here at all");
      }
    };
  });

  /* ==================================================================
     7. Walking a binary search tree four ways
     ================================================================== */

  reg("tree", function (api) {
    var KEYS = [50, 30, 70, 20, 40, 60, 80, 35, 45, 65, 75, 90];
    var nodes = [];
    (function build() {
      function insert(k) {
        if (!nodes.length) { nodes.push({ k: k, l: -1, r: -1 }); return; }
        var i = 0;
        for (;;) {
          if (k < nodes[i].k) {
            if (nodes[i].l < 0) { nodes.push({ k: k, l: -1, r: -1 }); nodes[i].l = nodes.length - 1; return; }
            i = nodes[i].l;
          } else {
            if (nodes[i].r < 0) { nodes.push({ k: k, l: -1, r: -1 }); nodes[i].r = nodes.length - 1; return; }
            i = nodes[i].r;
          }
        }
      }
      KEYS.forEach(insert);
    })();

    var order = "in";
    var seg = el("div", "seg");
    [["in", "in-order"], ["pre", "pre-order"], ["post", "post-order"], ["bfs", "level-order"]].forEach(function (o) {
      var b = api.button(o[1]);
      b.setAttribute("aria-pressed", o[0] === order ? "true" : "false");
      b.addEventListener("click", function () {
        order = o[0];
        Array.prototype.forEach.call(seg.children, function (c) { c.setAttribute("aria-pressed", c === b ? "true" : "false"); });
        api.rebuild();
      });
      seg.appendChild(b);
    });
    api.add(seg);

    var svg = el("div"), out = el("div", "cells");
    api.stage.appendChild(svg); api.stage.appendChild(el("p", "nojs", "visit order"));
    api.stage.appendChild(out);
    api.speed = 380;

    /* x by in-order rank, y by depth: the layout everyone draws by hand */
    var xr = {}, depth = {}, rank = 0;
    (function place(i, d) {
      if (i < 0) return;
      depth[i] = d;
      place(nodes[i].l, d + 1);
      xr[i] = rank++;
      place(nodes[i].r, d + 1);
    })(0, 0);
    var maxD = 0; for (var q in depth) maxD = Math.max(maxD, depth[q]);

    return {
      frames: function () {
        var F = [], seen = [], stack = [];
        function snap(cur, note) { F.push({ cur: cur, out: seen.slice(), stack: stack.slice(), note: note }); }
        snap(-1, "nothing visited yet");
        if (order === "bfs") {
          var qq = [0];
          while (qq.length) {
            var i = qq.shift();
            stack = qq.slice();
            snap(i, "take the front of the queue");
            seen.push(nodes[i].k);
            if (nodes[i].l >= 0) qq.push(nodes[i].l);
            if (nodes[i].r >= 0) qq.push(nodes[i].r);
            stack = qq.slice();
            snap(i, "visit " + nodes[i].k + ", then queue its children");
          }
        } else {
          (function walk(i) {
            if (i < 0) return;
            stack.push(i);
            snap(i, "descend into " + nodes[i].k);
            if (order === "pre") { seen.push(nodes[i].k); snap(i, "pre-order: visit on the way <b>down</b>"); }
            walk(nodes[i].l);
            if (order === "in") { seen.push(nodes[i].k); snap(i, "in-order: visit <b>between</b> the two subtrees"); }
            walk(nodes[i].r);
            if (order === "post") { seen.push(nodes[i].k); snap(i, "post-order: visit on the way <b>up</b>"); }
            stack.pop();
          })(0);
        }
        snap(-1, order === "in"
          ? "in-order on a search tree gives you the keys sorted &mdash; that is the whole trick"
          : order === "pre" ? "pre-order writes a tree you can rebuild by re-inserting in that order"
          : order === "post" ? "post-order frees children before parents, which is why destructors use it"
          : "level-order needs a queue, not the call stack &mdash; and it finds the shallowest node first");
        return F;
      },
      render: function (f) {
        var W = 660, H = 30 + (maxD + 1) * 48, parts = [];
        function pos(i) { return { x: 16 + xr[i] / (nodes.length - 1) * (W - 32), y: 20 + depth[i] * 48 }; }
        nodes.forEach(function (nd, i) {
          [nd.l, nd.r].forEach(function (c) {
            if (c < 0) return;
            var a = pos(i), b = pos(c);
            parts.push('<line class="edge" x1="' + a.x.toFixed(1) + '" y1="' + (a.y + 13) +
                       '" x2="' + b.x.toFixed(1) + '" y2="' + (b.y - 13) + '"/>');
          });
        });
        nodes.forEach(function (nd, i) {
          var p = pos(i), cls = "node";
          if (i === f.cur) cls += " hot";
          else if (f.out.indexOf(nd.k) >= 0) cls += " ok";
          else if (f.stack.indexOf(i) >= 0) cls += " on";
          parts.push('<g class="' + cls + '"><circle cx="' + p.x.toFixed(1) + '" cy="' + p.y +
                     '" r="14"/><text x="' + p.x.toFixed(1) + '" y="' + (p.y + 4) +
                     '" text-anchor="middle">' + nd.k + "</text></g>");
        });
        svg.innerHTML = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="A binary search tree with the current traversal highlighted">' + parts.join("") + "</svg>";
        out.innerHTML = f.out.map(function (k) { return '<span class="cell hit">' + k + "</span>"; }).join("") ||
                        '<span class="cell empty">&middot;</span>';
        api.say("<b>" + f.note + "</b> &nbsp;&middot;&nbsp; visited <span class='n'>" + f.out.length +
                "</span> of " + nodes.length + (f.stack.length ? " &nbsp; " + (order === "bfs" ? "queue" : "call stack") + " depth <span class='n'>" + f.stack.length + "</span>" : ""));
      }
    };
  });
"""

P3 = r"""
  /* ==================================================================
     8. Four searches over the same grid
     ================================================================== */

  reg("graph", function (api) {
    var W = 39, H = 15, OPEN = 0, WALL = 1, SLOW = 2;
    var kind = api.add(sel([["bfs", "breadth-first"], ["dfs", "depth-first"],
                            ["dij", "Dijkstra"], ["astar", "A* (Manhattan)"]], "bfs"));
    kind.setAttribute("aria-label", "Search");
    var clr = api.add(api.button("Clear walls"));
    kind.addEventListener("change", function () { api.rebuild(); });
    api.speed = 26;

    /* A fixed layout, not a random one: the figure has to look the same on
       every load, or the printed page depends on the dice. */
    var g = new Array(W * H), i, x, y;
    for (i = 0; i < W * H; i++) g[i] = OPEN;
    function box(x0, y0, x1, y1, v) {
      for (var yy = y0; yy <= y1; yy++) for (var xx = x0; xx <= x1; xx++) g[yy * W + xx] = v;
    }
    box(9, 0, 9, 9, WALL); box(17, 5, 17, 14, WALL);
    box(25, 0, 25, 8, WALL); box(25, 8, 32, 8, WALL);
    box(31, 9, 31, 14, WALL);
    box(19, 1, 24, 4, SLOW); box(27, 10, 36, 13, SLOW); box(11, 11, 16, 14, SLOW);
    var SRC = 7 * W + 1, DST = 7 * W + (W - 2);
    g[SRC] = OPEN; g[DST] = OPEN;

    var grid = el("div", "grid");
    grid.style.gridTemplateColumns = "repeat(" + W + ", var(--cs,17px))";
    var cellEls = [];
    for (i = 0; i < W * H; i++) {
      var b = document.createElement("b");
      b.setAttribute("data-i", i);
      grid.appendChild(b); cellEls.push(b);
    }
    api.stage.appendChild(grid);
    api.stage.appendChild(legend([["--l2", "expanded"], ["--l1", "shortest path"],
                                  ["--ink-soft", "wall"], ["--surface-2", "slow ground, costs 5"]]));
    var hint = el("p", "nojs", "Click a square to add or remove a wall.");
    hint.style.marginTop = "10px";
    api.stage.appendChild(hint);

    grid.addEventListener("click", function (e) {
      var t = e.target.getAttribute && e.target.getAttribute("data-i");
      if (t == null) return;
      var k = +t;
      if (k === SRC || k === DST) return;
      g[k] = g[k] === WALL ? OPEN : WALL;
      api.rebuild();
    });
    clr.addEventListener("click", function () {
      for (var k = 0; k < g.length; k++) if (g[k] === WALL) g[k] = OPEN;
      api.rebuild();
    });

    function nbrs(k) {
      var out = [], cx = k % W, cy = (k / W) | 0;
      if (cx > 0) out.push(k - 1);
      if (cx < W - 1) out.push(k + 1);
      if (cy > 0) out.push(k - W);
      if (cy < H - 1) out.push(k + W);
      return out;
    }
    function manhattan(k) {
      return Math.abs(k % W - DST % W) + Math.abs(((k / W) | 0) - ((DST / W) | 0));
    }

    var built = null;               /* the trace, so render can replay it */

    return {
      frames: function () {
        var weighted = kind.value === "dij" || kind.value === "astar";
        var cost = function (k) { return weighted && g[k] === SLOW ? 5 : 1; };
        var dist = {}, prev = {}, F = [], open = [SRC], seen = {}, expanded = 0;
        dist[SRC] = 0;
        var found = false;

        while (open.length) {
          var k;
          if (kind.value === "bfs") k = open.shift();
          else if (kind.value === "dfs") k = open.pop();
          else {
            /* a linear scan stands in for the priority queue: the point of the
               figure is the shape of the search, not the queue's constant */
            var best = 0;
            for (var q = 1; q < open.length; q++) {
              var f1 = dist[open[q]] + (kind.value === "astar" ? manhattan(open[q]) : 0);
              var f0 = dist[open[best]] + (kind.value === "astar" ? manhattan(open[best]) : 0);
              if (f1 < f0) best = q;
            }
            k = open.splice(best, 1)[0];
          }
          if (seen[k]) continue;
          seen[k] = 1; expanded++;
          F.push({ at: k, front: open.slice(), n: expanded, d: dist[k] });
          if (k === DST) { found = true; break; }
          nbrs(k).forEach(function (nb) {
            if (g[nb] === WALL || seen[nb]) return;
            var nd = dist[k] + cost(nb);
            if (dist[nb] == null || nd < dist[nb]) { dist[nb] = nd; prev[nb] = k; open.push(nb); }
          });
        }

        var path = [];
        if (found) {
          for (var p = DST; p != null; p = prev[p]) { path.unshift(p); if (p === SRC) break; }
          for (var s = 1; s <= path.length; s++) {
            F.push({ at: -1, front: [], n: expanded, path: path.slice(0, s), d: dist[DST] });
          }
        } else {
          F.push({ at: -1, front: [], n: expanded, path: [], blocked: true, d: 0 });
        }
        built = F;
        return F;
      },
      render: function (f, i, total) {
        /* Which cells have been expanded is the whole trace up to here, not
           something one frame carries -- replaying it is cheaper than storing
           a 585-cell snapshot per step. */
        var seen = {}, k;
        for (k = 0; k <= i && built; k++) { var a = built[k].at; if (a >= 0) seen[a] = 1; }
        var front = {}, path = {};
        f.front.forEach(function (x) { front[x] = 1; });
        (f.path || []).forEach(function (x) { path[x] = 1; });
        for (k = 0; k < cellEls.length; k++) {
          var c = g[k] === WALL ? "wall" : g[k] === SLOW ? "slow" : "";
          if (seen[k]) c += " seen";
          if (front[k]) c += " frontier";
          if (path[k]) c += " path";
          if (k === SRC) c += " src";
          if (k === DST) c += " dst";
          cellEls[k].className = c;
        }
        var names = { bfs: "Breadth-first", dfs: "Depth-first", dij: "Dijkstra", astar: "A*" };
        var lesson = {
          bfs: "expands in rings, so the first time it reaches the goal it has the fewest <b>steps</b> &mdash; but it ignores that the grey ground costs five",
          dfs: "commits to one direction until it hits something. It finds <em>a</em> path, not the shortest one",
          dij: "expands in order of cost, so it walks around the grey ground rather than through it &mdash; and pays by exploring nearly everywhere",
          astar: "is Dijkstra plus a guess at the distance remaining, so it leans towards the goal and expands a fraction of the cells"
        }[kind.value];
        api.say("<b>" + names[kind.value] + "</b> " + lesson +
                " &nbsp;&middot;&nbsp; cells expanded <span class='n'>" + f.n + "</span> of " +
                (W * H) + (f.path && f.path.length ? " &nbsp; path cost <span class='n'>" + f.d + "</span>" : "") +
                (f.blocked ? " &nbsp;&mdash; <b>no route: the goal is walled off</b>" : ""));
      }
    };
  });

  /* ==================================================================
     9. A dynamic programming table, filled cell by cell
     ================================================================== */

  reg("dp", function (api) {
    function inp(v) {
      var t = document.createElement("input");
      t.type = "text"; t.value = v; t.setAttribute("aria-label", "word");
      t.addEventListener("input", function () { api.rebuild(); });
      return t;
    }
    var A = inp("kitten"), B = inp("sitting");
    var la = el("label"); la.appendChild(document.createTextNode("from")); la.appendChild(A);
    var lb = el("label"); lb.appendChild(document.createTextNode("to")); lb.appendChild(B);
    api.add(la); api.add(lb);

    var host = el("div");
    api.stage.appendChild(host);
    api.speed = 90;

    return {
      frames: function () {
        var a = (A.value || "").slice(0, 10), b = (B.value || "").slice(0, 10);
        var n = a.length, m = b.length, F = [];
        var d = [];
        for (var i = 0; i <= n; i++) { d.push(new Array(m + 1)); }
        function snap(o) { o.d = d.map(function (r) { return r.slice(); }); o.a = a; o.b = b; F.push(o); }
        for (i = 0; i <= n; i++) { d[i][0] = i; }
        for (var j = 0; j <= m; j++) { d[0][j] = j; }
        snap({ note: "the edges are free: turning a word into the empty string costs one deletion per letter" });
        for (i = 1; i <= n; i++) {
          for (j = 1; j <= m; j++) {
            var same = a[i - 1] === b[j - 1];
            var del = d[i - 1][j] + 1, ins = d[i][j - 1] + 1, sub = d[i - 1][j - 1] + (same ? 0 : 1);
            d[i][j] = Math.min(del, ins, sub);
            snap({
              now: [i, j], deps: [[i - 1, j], [i, j - 1], [i - 1, j - 1]],
              note: same
                ? "<b>" + a[i - 1] + "</b> matches <b>" + b[j - 1] + "</b>, so carry the diagonal through for free: " + d[i][j]
                : "no match &mdash; cheapest of delete " + del + ", insert " + ins + ", substitute " + sub + " = <b>" + d[i][j] + "</b>"
            });
          }
        }
        var trace = [], ti = n, tj = m;
        while (ti > 0 || tj > 0) {
          trace.push([ti, tj]);
          if (ti > 0 && d[ti][tj] === d[ti - 1][tj] + 1) ti--;
          else if (tj > 0 && d[ti][tj] === d[ti][tj - 1] + 1) tj--;
          else { ti--; tj--; }
        }
        trace.push([0, 0]);
        for (var t = 0; t < trace.length; t++) {
          snap({ trace: trace.slice(0, t + 1), note: "walking back from the answer recovers the edits themselves, not just their number" });
        }
        snap({ trace: trace, done: true, note: "<b>" + d[n][m] + " edits</b> &mdash; and the table filled every subproblem exactly once" });
        return F;
      },
      render: function (f, i, total) {
        var a = f.a, b = f.b, n = a.length, m = b.length;
        var traceSet = {};
        (f.trace || []).forEach(function (p) { traceSet[p[0] + ":" + p[1]] = 1; });
        var depSet = {};
        (f.deps || []).forEach(function (p) { depSet[p[0] + ":" + p[1]] = 1; });
        var rows = ['<tr><th></th><th>&quot;&quot;</th>'];
        for (var j = 0; j < m; j++) rows.push("<th>" + b[j] + "</th>");
        rows.push("</tr>");
        for (var r = 0; r <= n; r++) {
          rows.push("<tr><th>" + (r === 0 ? "&quot;&quot;" : a[r - 1]) + "</th>");
          for (var c = 0; c <= m; c++) {
            var v = f.d[r][c], cls = v == null ? "" : "set";
            if (f.now && f.now[0] === r && f.now[1] === c) cls += " now";
            else if (depSet[r + ":" + c]) cls += " dep";
            if (traceSet[r + ":" + c]) cls = "trace";
            rows.push('<td class="' + cls + '">' + (v == null ? "" : v) + "</td>");
          }
          rows.push("</tr>");
        }
        host.innerHTML = '<table class="dp">' + rows.join("") + "</table>";
        api.say("<b>" + f.note + "</b> &nbsp;&middot;&nbsp; cells filled <span class='n'>" +
                Math.min(i, (n + 1) * (m + 1)) + "</span> of " + ((n + 1) * (m + 1)) +
                " &nbsp;&middot;&nbsp; the naive recursion would visit about <span class='n'>" +
                commas(Math.min(1e12, Math.pow(3, Math.min(n, 12)))) + "</span>");
      }
    };
  });

  /* ==================================================================
     10. Two pointers, and the window between them
     ================================================================== */

  reg("window", function (api) {
    var mode = api.add(sel([["uniq", "longest run with no repeat"],
                            ["sum", "two numbers that add to the target"]], "uniq"));
    mode.setAttribute("aria-label", "Problem");
    var box = document.createElement("input");
    box.type = "text"; box.value = "abcabcbbxyzzy"; box.style.width = "16ch";
    box.setAttribute("aria-label", "input");
    var lab = el("label"); lab.appendChild(document.createTextNode("input")); lab.appendChild(box);
    api.add(lab);
    mode.addEventListener("change", function () {
      box.value = mode.value === "uniq" ? "abcabcbbxyzzy" : "2 3 5 8 11 14 18 22 27";
      api.rebuild();
    });
    box.addEventListener("input", function () { api.rebuild(); });

    var ptr = el("div", "ptr"), cells = el("div", "cells"), idx = el("div", "idx");
    api.stage.appendChild(ptr); api.stage.appendChild(cells); api.stage.appendChild(idx);
    api.speed = 330;

    return {
      frames: function () {
        var F = [];
        if (mode.value === "uniq") {
          var s = (box.value || "").slice(0, 26), last = {}, lo = 0, best = 0, bestAt = 0;
          for (var hi = 0; hi < s.length; hi++) {
            var ch = s[hi];
            var jumped = last[ch] != null && last[ch] >= lo;
            if (jumped) lo = last[ch] + 1;
            last[ch] = hi;
            if (hi - lo + 1 > best) { best = hi - lo + 1; bestAt = lo; }
            F.push({ s: s.split(""), lo: lo, hi: hi, best: best, bestAt: bestAt,
                     note: jumped ? "<b>" + ch + "</b> is already in the window &mdash; drag the left edge past its last position"
                                  : "<b>" + ch + "</b> is new: the window just got longer" });
          }
          F.push({ s: s.split(""), lo: bestAt, hi: bestAt + best - 1, best: best, bestAt: bestAt, done: true,
                   note: "every index entered the window once and left once &mdash; that is why this is O(n), not O(n<sup>2</sup>)" });
        } else {
          var nums = (box.value || "").split(/[^0-9-]+/).filter(function (x) { return x !== ""; }).map(Number).slice(0, 22);
          nums.sort(function (p, q) { return p - q; });
          var target = nums.length > 3 ? nums[1] + nums[nums.length - 2] : 0;
          var l = 0, r = nums.length - 1;
          while (l < r) {
            var sum = nums[l] + nums[r];
            F.push({ s: nums, lo: l, hi: r, target: target, sum: sum,
                     note: sum === target ? "<b>" + nums[l] + " + " + nums[r] + " = " + target + "</b>"
                         : sum < target ? "sum is " + sum + ", too small &mdash; only moving <b>left</b> rightwards can help"
                         : "sum is " + sum + ", too big &mdash; only moving <b>right</b> leftwards can help" });
            if (sum === target) break;
            if (sum < target) l++; else r--;
          }
          F.push({ s: nums, lo: l, hi: r, target: target, sum: nums[l] + nums[r], done: true,
                   note: "each step throws away a whole row or column of the pair table &mdash; n steps instead of n<sup>2</sup>" });
        }
        return F;
      },
      render: function (f) {
        var top = [], cs = [], ix = [];
        for (var k = 0; k < f.s.length; k++) {
          var cls = "cell";
          if (k < f.lo || k > f.hi) cls += " out";
          else if (f.done) cls += " hit";
          else cls += " on";
          cs.push('<span class="' + cls + '">' + f.s[k] + "</span>");
          var tag = k === f.lo && k === f.hi ? "both" : k === f.lo ? "lo" : k === f.hi ? "hi" : "";
          top.push('<span style="color:var(--' + (tag ? "l2" : "ink-faint") + ')">' + tag + "</span>");
          ix.push("<span>" + (k % 5 === 0 ? k : "") + "</span>");
        }
        ptr.innerHTML = top.join(""); cells.innerHTML = cs.join(""); idx.innerHTML = ix.join("");
        api.say(f.note + " &nbsp;&middot;&nbsp; " + (f.target != null
          ? "target <span class='n'>" + f.target + "</span> &nbsp; current sum <span class='n'>" + f.sum + "</span>"
          : "window <span class='n'>" + (f.hi - f.lo + 1) + "</span> &nbsp; best so far <span class='n'>" + f.best + "</span>"));
      }
    };
  });

  /* ==================================================================
     11. Union-find, and what path compression actually does
     ================================================================== */

  reg("uf", function (api) {
    var N = 12;
    var PAIRS = [[0, 1], [2, 3], [4, 5], [1, 2], [6, 7], [8, 9], [5, 6], [3, 4], [10, 11], [9, 10], [7, 8], [0, 11]];
    var compress = true;
    var tog = api.add(api.button("path compression: on"));
    tog.setAttribute("aria-pressed", "true");
    tog.addEventListener("click", function () {
      compress = !compress;
      tog.textContent = "path compression: " + (compress ? "on" : "off");
      tog.setAttribute("aria-pressed", compress ? "true" : "false");
      api.rebuild();
    });
    var svg = el("div"), arr = el("div", "cells"), idx = el("div", "idx");
    api.stage.appendChild(svg);
    api.stage.appendChild(el("p", "nojs", "parent[i]"));
    api.stage.appendChild(arr); api.stage.appendChild(idx);
    api.speed = 340;

    return {
      start: function (F) { return Math.floor(F.length * 0.45); },
      frames: function () {
        var p = [], sz = [], F = [], hops = 0, i;
        for (i = 0; i < N; i++) { p.push(i); sz.push(1); }
        function snap(o) { o = o || {}; o.p = p.slice(); o.hops = hops; F.push(o); }
        snap({ note: "twelve elements, twelve components" });
        PAIRS.forEach(function (pr) {
          var roots = [];
          pr.forEach(function (start) {
            var path = [start], x = start;
            while (p[x] !== x) { x = p[x]; path.push(x); hops++; snap({ walk: path.slice(), note: "walk up from " + start + " looking for its root" }); }
            if (path.length === 1) snap({ walk: path.slice(), note: start + " is its own root" });
            if (compress && path.length > 2) {
              path.forEach(function (q) { p[q] = x; });
              snap({ walk: path.slice(), note: "<b>compress</b>: every node on that walk now points straight at " + x });
            }
            roots.push(x);
          });
          if (roots[0] === roots[1]) { snap({ note: pr[0] + " and " + pr[1] + " were already connected &mdash; nothing to do" }); return; }
          var a = roots[0], b = roots[1];
          if (sz[a] < sz[b]) { var t = a; a = b; b = t; }        /* union by size */
          p[b] = a; sz[a] += sz[b];
          snap({ walk: [b, a], note: "<b>union</b>: the smaller tree (" + sz[b] + ") hangs under the bigger root " + a });
        });
        snap({ note: compress
          ? "after compression almost everything points straight at a root, so find is effectively O(1)"
          : "without compression the trees stay tall, and every find pays for it again" });
        return F;
      },
      render: function (f) {
        var p = f.p, kids = [], roots = [], i;
        for (i = 0; i < N; i++) kids.push([]);
        for (i = 0; i < N; i++) { if (p[i] === i) roots.push(i); else kids[p[i]].push(i); }
        var xr = {}, dep = {}, rank = 0, maxD = 0;
        (function lay(list, d) {
          list.forEach(function (r) {
            dep[r] = d; maxD = Math.max(maxD, d);
            if (!kids[r].length) { xr[r] = rank++; return; }
            var first = rank;
            lay(kids[r], d + 1);
            xr[r] = (first + rank - 1) / 2;
          });
        })(roots, 0);
        var W = 660, H = 26 + (maxD + 1) * 44, span = Math.max(1, rank - 1), parts = [];
        function pos(k) { return { x: 16 + xr[k] / span * (W - 32), y: 18 + dep[k] * 44 }; }
        var walk = {};
        (f.walk || []).forEach(function (k) { walk[k] = 1; });
        for (i = 0; i < N; i++) {
          if (p[i] === i) continue;
          var a = pos(i), b = pos(p[i]);
          parts.push('<line class="edge' + (walk[i] && walk[p[i]] ? " on" : "") + '" x1="' + a.x.toFixed(1) +
                     '" y1="' + (a.y - 12) + '" x2="' + b.x.toFixed(1) + '" y2="' + (b.y + 12) + '"/>');
        }
        for (i = 0; i < N; i++) {
          var q = pos(i), cls = "node";
          if (walk[i]) cls += " hot";
          else if (p[i] === i) cls += " ok";
          parts.push('<g class="' + cls + '"><circle cx="' + q.x.toFixed(1) + '" cy="' + q.y +
                     '" r="13"/><text x="' + q.x.toFixed(1) + '" y="' + (q.y + 4) + '" text-anchor="middle">' + i + "</text></g>");
        }
        svg.innerHTML = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="The union-find forest">' + parts.join("") + "</svg>";
        var cs = [], ix = [];
        for (i = 0; i < N; i++) {
          cs.push('<span class="cell ' + (walk[i] ? "warn" : p[i] === i ? "hit" : "") + '">' + p[i] + "</span>");
          ix.push("<span>" + i + "</span>");
        }
        arr.innerHTML = cs.join(""); idx.innerHTML = ix.join("");
        api.say("<b>" + f.note + "</b> &nbsp;&middot;&nbsp; components <span class='n'>" + roots.length +
                "</span> &nbsp; tallest tree <span class='n'>" + (maxD + 1) +
                "</span> &nbsp; parent hops paid so far <span class='n'>" + f.hops + "</span>");
      }
    };
  });

  /* ---------- boot ---------- */
  function boot() {
    Array.prototype.forEach.call(document.querySelectorAll("figure.demo[data-demo]"), function (f) {
      f.tabIndex = 0;                    /* so the arrow keys and space reach it */
      try { mount(f); }
      catch (e) { if (window.console) console.error("demo " + f.getAttribute("data-demo"), e); }
    });
  }
  if (document.readyState === "complete") boot();
  else window.addEventListener("load", boot);
})();
</script>
"""

JS = P1 + P2 + P3
