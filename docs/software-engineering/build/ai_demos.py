# -*- coding: utf-8 -*-
"""The interactive figures on the AI engineering page.

Fifteen demos on top of the shared player in demo_ui.py, in plain JavaScript
with no dependencies, so the page keeps the series' promise: nothing is fetched
at runtime and the whole thing works off a memory stick.

Two shapes of figure appear here. Some are *traces* -- the attention sweep, the
index walk, the agent loop, the scheduler -- run once up front and recorded
frame by frame, so the reader can step backwards and the opening state is
deterministic. The rest are *calculators*: a panel of knobs at the top of the
stage and a picture underneath that recomputes as they move. The calculators
matter more here than they did on the algorithms page, because most of what an
AI engineer is asked in an interview is arithmetic with a shape to it -- how
much memory, how many tokens, how much money, what happens to recall.

Nothing autoplays, nothing is drawn on a canvas, and every number on the page
is computed from the formula printed beside it rather than quoted from a vendor.
Where a figure needs a price or a hardware size it says so and uses a round
illustrative number.
"""

import demo_ui

D0 = r"""

  /* ==================================================================
     Knobs: the calculator figures' control panel
     ==================================================================
     A demo that is steered rather than played gets one of these at the top of
     its stage. Each control writes into a plain object the demo reads, then
     calls back so it can repaint. The panel lives above the body element and
     is built once, so a repaint never destroys the control the reader is
     dragging. */

  function knobs(api) {
    var box = el("div", "knobs");
    api.stage.appendChild(box);

    function shell(label, node, valueNode) {
      var l = el("label");
      var head = el("span", null, label);
      if (valueNode) { head.appendChild(document.createTextNode(" ")); head.appendChild(valueNode); }
      l.appendChild(head);
      l.appendChild(node);
      box.appendChild(l);
      return l;
    }

    return {
      box: box,
      /* a slider; `fmt` renders the live value beside the label */
      range: function (label, min, max, val, step, fmt, on) {
        var r = document.createElement("input");
        r.type = "range"; r.min = min; r.max = max; r.step = step; r.value = val;
        r.setAttribute("aria-label", label);
        var v = el("span", "v", fmt(+val));
        r.addEventListener("input", function () { v.textContent = fmt(+r.value); on(+r.value); });
        shell(label, r, v);
        return { get: function () { return +r.value; },
                 set: function (x) { r.value = x; v.textContent = fmt(+r.value); } };
      },
      /* a dropdown, for things with names rather than magnitudes */
      pick: function (label, options, value, on) {
        var s = sel(options, value);
        s.setAttribute("aria-label", label);
        s.addEventListener("change", function () { on(s.value); });
        shell(label, s, null);
        return { get: function () { return s.value; } };
      },
      /* two or three mutually exclusive choices, wide enough to read */
      sw: function (label, options, value, on) {
        var wrap = el("div", "sw"), cur = value, made = [];
        options.forEach(function (o) {
          var b = btn(o[1]);
          b.setAttribute("aria-pressed", o[0] === cur ? "true" : "false");
          b.addEventListener("click", function () {
            cur = o[0];
            made.forEach(function (x) { x[1].setAttribute("aria-pressed", x[0] === cur ? "true" : "false"); });
            on(cur);
          });
          made.push([o[0], b]);
          wrap.appendChild(b);
        });
        shell(label, wrap, null);
        return { get: function () { return cur; } };
      }
    };
  }

  /* Numbers, formatted the way the readout lines want them. */
  function round(x, n) { var p = Math.pow(10, n); return Math.round(x * p) / p; }
  function big(n) {
    if (n >= 1e12) return round(n / 1e12, 2) + "T";
    if (n >= 1e9) return round(n / 1e9, 2) + "B";
    if (n >= 1e6) return round(n / 1e6, 2) + "M";
    if (n >= 1e3) return round(n / 1e3, 1) + "k";
    return String(Math.round(n));
  }
  function gb(bytes) {
    if (bytes >= 1099511627776) return round(bytes / 1099511627776, 2) + " TB";
    if (bytes >= 1073741824) return round(bytes / 1073741824, 1) + " GB";
    if (bytes >= 1048576) return round(bytes / 1048576, 1) + " MB";
    return round(bytes / 1024, 1) + " KB";
  }
  function money(x) {
    if (x >= 1000) return "$" + commas(Math.round(x));
    if (x >= 1) return "$" + round(x, 2);
    if (x >= 0.01) return "$" + round(x, 3);
    return "$" + x.toFixed(5).replace(/0+$/, "");
  }
  function pct(x) { return round(x * 100, 1) + "%"; }
  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
"""


D1 = r"""

  /* ==================================================================
     1. Tokens
     ==================================================================
     A real tokenizer's vocabulary is *learned*: byte-pair encoding starts from
     bytes and repeatedly merges the commonest adjacent pair until it has fifty
     to two hundred thousand entries. Shipping that table would be a megabyte,
     so this figure fakes the vocabulary with rules and keeps the three
     behaviours that actually matter to a reader: a common word is one token,
     an unusual one shatters, and the leading space belongs to the word after
     it, not the word before. The caption says so. */

  var COMMON = ("the a an and or but if then of to in on at for with from by as is are was were be " +
    "been being have has had do does did will would can could should may might must not no yes it " +
    "its this that these those i you he she we they me him her us them my your his our their there " +
    "here what which who when where why how all any both each few more most other some such only own " +
    "same so than too very just now new old first last long great little way day time year people " +
    "man woman child work life world thing part place case week month home water word name number " +
    "line end back over under after before between about into out up down off again once because " +
    "while during through against above below same next good bad big small high low right left " +
    "make made get got go went come came take took see saw know knew think thought say said tell " +
    "told give gave find found use used want need try ask call keep let put run set show move live " +
    "model token data text code file user query answer system prompt context memory search cost " +
    "size cache batch server client request response error test train"
  ).split(" ");

  function utf8len(s) {
    return encodeURIComponent(s).replace(/%[0-9A-Fa-f]{2}/g, "x").length;
  }

  /* An unlearned word breaks into pieces of three to five characters, which is
     about what a byte-pair vocabulary does to a word it has never merged. */
  function chop(w, head) {
    var out = [], i = 0;
    while (i < w.length) {
      var n = Math.min(4, w.length - i);
      if (w.length - i - n === 1) n += 1;          /* never strand a single letter */
      out.push((i === 0 ? head : "") + w.slice(i, i + n));
      i += n;
    }
    return out;
  }

  function tokenize(text) {
    var out = [];
    var re = /(\s*)(\r?\n|[A-Za-z]+|[0-9]+|[\uD800-\uDBFF][\uDC00-\uDFFF]|[^\sA-Za-z0-9])/g, m;
    while ((m = re.exec(text))) {
      var lead = m[1] || "", piece = m[2], i;
      if (/^\r?\n$/.test(piece)) { out.push(lead + piece); continue; }
      if (/^[0-9]+$/.test(piece)) {                /* digits in groups of up to three */
        var first = piece.length % 3 || 3, chunks = [piece.slice(0, first)];
        for (i = first; i < piece.length; i += 3) chunks.push(piece.slice(i, i + 3));
        chunks[0] = lead + chunks[0];
        out = out.concat(chunks);
        continue;
      }
      if (/^[A-Za-z]+$/.test(piece)) {
        var subs = piece.split(/(?=[A-Z])/).filter(Boolean), head = lead;
        for (i = 0; i < subs.length; i++) {
          var w = subs[i], low = w.toLowerCase();
          if (COMMON.indexOf(low) >= 0 && w.length <= 9) out.push(head + w);
          else out = out.concat(chop(w, head));
          head = "";
        }
        continue;
      }
      out.push(lead + piece);                      /* punctuation and everything else */
    }
    return out;
  }

  var SAMPLES = [
    ["plain", "Plain English"],
    ["code", "A line of code"],
    ["log", "A log line"],
    ["json", "A JSON payload"],
    ["intl", "Not English"]
  ];
  var TEXT = {
    plain: "The quick brown fox jumps over the lazy dog.",
    code: "def cosine(a, b): return dot(a, b) / (norm(a) * norm(b))",
    log: "2026-08-30T14:22:09Z ERR svc=checkout trace_id=9f3b2a71c4 status=502",
    json: '{"model": "gpt-x", "temperature": 0.2, "max_tokens": 1024}',
    intl: "Mach dir keine Sorgen — 心配しないで 🙂"
  };

  reg("tokens", function (api) {
    var text = TEXT.plain;
    var box = el("div"), toks = el("div", "toks");
    box.appendChild(toks);
    api.stage.appendChild(box);

    var pick = api.select(SAMPLES, "plain");
    pick.setAttribute("aria-label", "Sample text");
    var input = document.createElement("input");
    input.type = "text"; input.className = "wide"; input.value = text;
    input.setAttribute("aria-label", "Text to tokenize");
    pick.addEventListener("change", function () {
      text = TEXT[pick.value]; input.value = text; api.rebuild();
    });
    input.addEventListener("input", function () { text = input.value; api.rebuild(); });
    api.add(pick); api.add(input);

    return {
      render: function () {
        var t = tokenize(text), out = [], i;
        for (i = 0; i < t.length; i++) {
          var b = utf8len(t[i]);
          out.push('<span class="tok' + (i % 2 ? " alt" : "") + '">' +
                   esc(t[i]).replace(/ /g, "·").replace(/\n/g, "↵") +
                   (b > t[i].length ? "<i>" + b + "B</i>" : "") + "</span>");
        }
        toks.innerHTML = out.join("") || '<span class="tok sp">(empty)</span>';
        var chars = text.length, n = t.length || 1;
        /* Frontier-tier input pricing, as published for Claude Opus 5 in
           August 2026. Prices move; the shape of the arithmetic does not. */
        api.say("<b>" + commas(chars) + "</b> characters &rarr; <span class='n'>" + commas(t.length) +
          "</span> tokens &nbsp;&middot;&nbsp; <span class='n'>" + round(chars / n, 2) +
          "</span> characters per token &nbsp;&middot;&nbsp; at $5 / M input tokens this prompt costs <span class='n'>" +
          money(t.length * 5 / 1e6) + "</span> to send, every time you send it");
      }
    };
  });

  /* ==================================================================
     2. Embeddings
     ==================================================================
     Two dimensions instead of a thousand, and the words are placed by hand.
     What survives the shrinking is the only thing the figure is trying to
     teach: cosine reads the *angle* from the origin and is blind to length,
     which is why a vector and twice that vector are the same point to it. */

  var WORDS = [
    ["apple", 12, 95], ["banana", 20, 78], ["mango", 28, 88], ["pear", 6, 70],
    ["dog", 92, 100], ["puppy", 92, 46], ["cat", 84, 86], ["horse", 101, 74],
    ["Paris", 168, 92], ["London", 176, 80], ["Tokyo", 185, 96], ["Berlin", 160, 68],
    ["python", 252, 90], ["compiler", 262, 76], ["kernel", 244, 84], ["bytecode", 270, 62],
    ["invoice", 322, 88], ["refund", 331, 72], ["payment", 314, 94], ["tax", 338, 60]
  ];

  reg("embed", function (api) {
    var query = "puppy", metric = "cos";
    var wrap = el("div", "growth"), left = el("div"), right = el("div");
    wrap.appendChild(left); wrap.appendChild(right);

    var k = knobs(api);
    api.stage.appendChild(wrap);
    k.pick("Query word", WORDS.map(function (w) { return [w[0], w[0]]; }), query,
           function (v) { query = v; api.rebuild(); });
    k.sw("Ranked by", [["cos", "Cosine"], ["euc", "Distance"]], metric,
         function (v) { metric = v; api.rebuild(); });

    function vec(w) {
      var a = w[1] * Math.PI / 180;
      return { x: Math.cos(a) * w[2], y: Math.sin(a) * w[2] };
    }

    return {
      render: function () {
        var q = WORDS.filter(function (w) { return w[0] === query; })[0], qv = vec(q);
        var scored = WORDS.map(function (w) {
          var v = vec(w);
          var cos = (qv.x * v.x + qv.y * v.y) /
                    (Math.sqrt(qv.x * qv.x + qv.y * qv.y) * Math.sqrt(v.x * v.x + v.y * v.y));
          var euc = Math.sqrt((qv.x - v.x) * (qv.x - v.x) + (qv.y - v.y) * (qv.y - v.y));
          return { w: w, v: v, cos: cos, euc: euc };
        });
        var rank = scored.slice().sort(function (a, b) {
          return metric === "cos" ? b.cos - a.cos : a.euc - b.euc;
        }).filter(function (s) { return s.w[0] !== query; });
        var top = {}, i;
        for (i = 0; i < 3; i++) top[rank[i].w[0]] = 1;

        var W = 330, H = 300, cx = W / 2, cy = H / 2, S = 1.32;
        var p = ["<circle cx='" + cx + "' cy='" + cy + "' r='2.5' fill='currentColor'/>"];
        p.push("<line class='edge' x1='14' y1='" + cy + "' x2='" + (W - 14) + "' y2='" + cy + "'/>");
        p.push("<line class='edge' x1='" + cx + "' y1='14' x2='" + cx + "' y2='" + (H - 14) + "'/>");
        scored.forEach(function (s) {
          var x = cx + s.v.x * S, y = cy - s.v.y * S;
          var hot = s.w[0] === query, near = top[s.w[0]];
          if (hot || near) p.push("<line class='edge" + (hot ? " on" : "") + "' x1='" + cx + "' y1='" + cy +
            "' x2='" + x.toFixed(1) + "' y2='" + y.toFixed(1) + "'/>");
          p.push("<g class='node" + (hot ? " hot" : near ? " on" : "") + "'><circle cx='" + x.toFixed(1) +
            "' cy='" + y.toFixed(1) + "' r='4'/><text x='" + (x + (s.v.x < 0 ? -7 : 7)).toFixed(1) +
            "' y='" + (y + 4).toFixed(1) + "' text-anchor='" + (s.v.x < 0 ? "end" : "start") + "'>" +
            s.w[0] + "</text></g>");
        });
        left.innerHTML = "<svg viewBox='0 0 " + W + " " + H +
          "' role='img' aria-label='Twenty words as vectors from the origin'>" + p.join("") + "</svg>";

        var rows = ["<tr><th>Neighbour</th><th>cosine</th><th>distance</th></tr>"];
        for (i = 0; i < 8; i++) {
          var s = rank[i];
          rows.push("<tr class='" + (i < 3 ? "fine" : "") + "'><td>" + s.w[0] + "</td><td>" +
            s.cos.toFixed(3) + "</td><td>" + s.euc.toFixed(0) + "</td></tr>");
        }
        right.innerHTML = "<table class='gtab'>" + rows.join("") + "</table>";

        var same = scored.filter(function (s) { return s.w[0] !== query && s.cos > 0.9999; });
        api.say("Nearest to <b>" + query + "</b> by " + (metric === "cos" ? "cosine" : "Euclidean distance") +
          ": <span class='n'>" + rank.slice(0, 3).map(function (s) { return s.w[0]; }).join(", ") +
          "</span>" + (same.length ? " &nbsp;&middot;&nbsp; <b>" + same[0].w[0] +
          "</b> scores <span class='n'>1.000</span> &mdash; it lies on the same ray, and cosine cannot see length" : ""));
      }
    };
  });
"""


D2 = r"""

  /* ==================================================================
     3. Attention
     ==================================================================
     Attention is one line of arithmetic -- softmax(QK^T / sqrt(d)) V -- and
     the only part a reader needs to see is the matrix in the middle: for every
     token, how much of every other token it reads. Real heads are learned, so
     the three here are hand-built to be the three that are actually found in
     trained models: one that looks one token back, one that resolves what a
     pronoun refers to, and one that dumps its unused mass on the first token.
     That last one is real and has a name -- the attention sink. */

  var SENT = ["The", "cat", "sat", "on", "the", "mat", "because", "it", "was", "warm", "."];
  var CONTENT = { cat: 1, sat: 1, mat: 1, warm: 1, it: 1, was: 1 };
  var LINKS = {                                  /* query index -> {key index: pull} */
    7: { 1: 6.0, 5: 3.4 },                       /* "it" -> "cat", and weakly "mat" */
    9: { 5: 3.0, 1: 2.0, 7: 2.6 },               /* "warm" -> "mat", "it" */
    8: { 7: 3.2, 1: 1.4 },                       /* "was" -> "it" */
    5: { 3: 2.4, 1: 1.2 },                       /* "mat" -> "on" */
    2: { 1: 3.6 }                                /* "sat" -> "cat" */
  };
  var HEADS = [
    ["prev", "Looks one back"],
    ["ref", "Resolves the pronoun"],
    ["sink", "Parks on token 0"]
  ];

  function attnScores(head, i) {
    var s = [], j;
    for (j = 0; j < SENT.length; j++) {
      var v = 0;
      if (head === "prev") v = j === i - 1 ? 6 : j === i ? 1.2 : 0.2;
      else if (head === "sink") v = j === 0 ? 5.2 : j === i ? 1.6 : 0.3;
      else {
        v = CONTENT[SENT[j].toLowerCase()] ? 0.9 : 0.2;
        if (LINKS[i] && LINKS[i][j] != null) v = LINKS[i][j];
        if (j === i) v = 1.1;
      }
      s.push(v);
    }
    return s;
  }
  function softmaxMasked(s, i, causal) {
    var out = [], sum = 0, j;
    for (j = 0; j < s.length; j++) {
      var ok = !causal || j <= i;
      var e = ok ? Math.exp(s[j]) : 0;
      out.push(e); sum += e;
    }
    for (j = 0; j < out.length; j++) out[j] = sum ? out[j] / sum : 0;
    return out;
  }

  reg("attention", function (api) {
    var head = "ref", causal = true;
    var body = el("div");
    var k = knobs(api);
    api.stage.appendChild(body);
    k.pick("Head", HEADS, head, function (v) { head = v; api.rebuild(true); });
    k.sw("Mask", [["on", "Causal"], ["off", "None"]], "on",
         function (v) { causal = v === "on"; api.rebuild(true); });
    api.speed = 420;

    return {
      /* one frame per query token: the row the model is computing */
      frames: function () {
        var F = [], i;
        for (i = 0; i < SENT.length; i++) F.push(i);
        return F;
      },
      start: function () { return 7; },          /* open on "it", the interesting row */
      render: function (row) {
        var i, j, head_cells = ["<tr><th></th>"];
        for (j = 0; j < SENT.length; j++) head_cells.push("<th>" + esc(SENT[j]) + "</th>");
        head_cells.push("</tr>");
        var rows = [head_cells.join("")];
        var peakJ = 0, peakV = 0;
        /* the row's peak has to be known before its cells are drawn, or the
           outline lands on every new running maximum instead of the winner */
        var pw = softmaxMasked(attnScores(head, row), row, causal);
        for (j = 0; j < pw.length; j++) if (pw[j] > peakV) { peakV = pw[j]; peakJ = j; }
        for (i = 0; i < SENT.length; i++) {
          var w = softmaxMasked(attnScores(head, i), i, causal);
          var cells = ["<tr class='" + (i === row ? "on" : "") + "'><th class='r'>" + esc(SENT[i]) + "</th>"];
          for (j = 0; j < SENT.length; j++) {
            var v = w[j], zero = v < 0.005;
            cells.push("<td class='" + (zero ? "z" : "") + (i === row && j === peakJ && v > 0.05 ? " pk" : "") +
              "' style='background:color-mix(in srgb,var(--l2) " + Math.round(v * 88) + "%,var(--surface))'>" +
              (zero ? "" : Math.round(v * 100)) + "</td>");
          }
          cells.push("</tr>");
          rows.push(cells.join(""));
        }
        body.innerHTML = "<table class='mat'>" + rows.join("") + "</table>";
        api.say("Row <span class='n'>" + row + "</span> &mdash; the token <b>" + SENT[row] +
          "</b> reads the sentence. Its largest share, <span class='n'>" + Math.round(peakV * 100) +
          "%</span>, goes to <b>" + SENT[peakJ] + "</b>." +
          (causal ? " Everything to the right of the diagonal is masked out: during training the model must not see what it is about to predict."
                  : " With the mask off, every token sees the whole sentence &mdash; which is what an embedding model does, and what a generator cannot."));
      }
    };
  });

  /* ==================================================================
     4. Sampling
     ==================================================================
     The model's output is a probability distribution over the whole
     vocabulary. Temperature reshapes it, top-k and top-p cut its tail, and
     only then is one token drawn. Getting these three straight is worth a
     question in almost every interview, because the usual mental model --
     "temperature is creativity" -- gets the mechanism backwards. */

  var CAND = [
    ["Paris", 9.2], [" the", 4.1], [" a", 3.2], [" located", 3.0], [" home", 2.6],
    [" one", 2.4], [" Lyon", 1.9], [" actually", 1.6], [" called", 1.4], [" now", 1.2],
    [" Marseille", 0.9], [" France", 0.4], [" banana", -2.1]
  ];

  reg("sampling", function (api) {
    var T = 0.8, topP = 1, topK = 0;
    var body = el("div", "dist");
    var k = knobs(api);
    api.stage.appendChild(body);
    k.range("Temperature", 0.05, 2, T, 0.05, function (v) { return v <= 0.05 ? "0.05 (greedy)" : v.toFixed(2); },
            function (v) { T = v; api.rebuild(); });
    k.range("Top-p", 0.05, 1, topP, 0.01, function (v) { return v >= 1 ? "1.00 (off)" : v.toFixed(2); },
            function (v) { topP = v; api.rebuild(); });
    k.range("Top-k", 0, CAND.length, topK, 1, function (v) { return v === 0 ? "off" : String(v); },
            function (v) { topK = v; api.rebuild(); });

    return {
      render: function () {
        var ex = CAND.map(function (c) { return { t: c[0], e: Math.exp(c[1] / T) }; });
        var sum = ex.reduce(function (a, b) { return a + b.e; }, 0);
        ex.forEach(function (c) { c.p = c.e / sum; });
        ex.sort(function (a, b) { return b.p - a.p; });

        var cum = 0, kept = [], i;
        for (i = 0; i < ex.length; i++) {
          var inK = !topK || i < topK;
          var inP = cum < topP - 1e-9;
          ex[i].keep = inK && inP;
          if (ex[i].keep) { kept.push(ex[i]); cum += ex[i].p; }
        }
        var ksum = kept.reduce(function (a, b) { return a + b.p; }, 0);
        var H = 0;
        kept.forEach(function (c) { var q = c.p / ksum; if (q > 0) H -= q * Math.log(q) / Math.LN2; });

        var out = [], max = ex[0].p;
        ex.forEach(function (c) {
          var shown = c.keep ? c.p / ksum : c.p;
          out.push("<div class='d" + (c.keep ? "" : " cut") + (c === ex[0] && c.keep ? " pick" : "") +
            "'><span class='t'>" + esc(c.t.replace(/^ /, "·")) + "</span><span class='b'><span style='width:" +
            (100 * c.p / max).toFixed(1) + "%'></span></span><span class='v'>" +
            (shown * 100).toFixed(shown < 0.01 ? 2 : 1) + "%</span></div>");
        });
        body.innerHTML = out.join("");
        api.say("Kept <span class='n'>" + kept.length + "</span> of " + CAND.length +
          " candidates &nbsp;&middot;&nbsp; the top one now holds <span class='n'>" +
          pct(kept[0].p / ksum) + "</span> &nbsp;&middot;&nbsp; entropy <span class='n'>" +
          round(H, 2) + "</span> bits" +
          (T <= 0.1 ? " &mdash; at this temperature the distribution has collapsed onto one token, which is greedy decoding under another name."
           : T >= 1.5 ? " &mdash; high temperature has flattened the distribution so far that <b>banana</b> is now reachable. Temperature does not add ideas; it only redistributes probability the model already assigned."
           : ""));
      }
    };
  });
"""


D3 = r"""

  /* ==================================================================
     5. The context budget
     ==================================================================
     A context window is not storage, it is a per-request budget that is spent
     again on every request. The figure exists to make one habit automatic:
     before asking "does it fit", add up what is already in there. */

  var WINDOWS = [["8000", "8k"], ["32000", "32k"], ["128000", "128k"],
                 ["200000", "200k"], ["1000000", "1M"]];

  reg("budget", function (api) {
    var win = 128000, turns = 12, chunks = 6, csize = 600, tools = 12;
    var body = el("div");
    var k = knobs(api);
    api.stage.appendChild(body);
    var re = function () { api.rebuild(); };
    k.pick("Context window", WINDOWS, "128000", function (v) { win = +v; re(); });
    k.range("Tool definitions", 0, 40, tools, 1, function (v) { return String(v); },
            function (v) { tools = v; re(); });
    k.range("Conversation turns", 0, 40, turns, 1, function (v) { return String(v); },
            function (v) { turns = v; re(); });
    k.range("Retrieved chunks", 0, 20, chunks, 1, function (v) { return String(v); },
            function (v) { chunks = v; re(); });
    k.range("Chunk size", 200, 1400, csize, 50, function (v) { return v + " tok"; },
            function (v) { csize = v; re(); });

    return {
      render: function () {
        var parts = [
          ["s1", "System prompt", 900],
          ["s2", "Tool definitions", tools * 180],
          ["s3", "Conversation", turns * 320],
          ["s4", "Retrieved chunks", chunks * csize],
          ["s5", "Room for the answer", 1500]
        ];
        var used = parts.reduce(function (a, p) { return a + p[2]; }, 0);
        var scale = Math.max(used, win);
        var bar = parts.map(function (p) {
          return "<i class='" + p[0] + "' style='width:" + (100 * p[2] / scale).toFixed(2) + "%'></i>";
        });
        if (used < win) bar.push("<i style='width:" + (100 * (win - used) / scale).toFixed(2) + "%'></i>");
        else if (used > win) bar.push("");
        var key = parts.map(function (p) {
          return "<span><i class='" + p[0] + "'></i>" + p[1] + " <b>" + commas(p[2]) + "</b></span>";
        });
        var over = used - win;
        body.innerHTML = "<div class='stack'>" + bar.join("") +
          (over > 0 ? "<i class='over' style='width:" + (100 * over / scale).toFixed(2) + "%'></i>" : "") +
          "</div><div class='stack-key'>" + key.join("") +
          "<span><i style='background:var(--surface-2)'></i>Window <b>" + commas(win) + "</b></span></div>";
        api.say(over > 0
          ? "<b>Over by " + commas(over) + " tokens.</b> The request is rejected, or something silently gets dropped &mdash; usually the oldest turns, which is how an assistant forgets what you told it at the start."
          : "<span class='n'>" + commas(used) + "</span> of " + commas(win) + " tokens &nbsp;&middot;&nbsp; <span class='n'>" +
            pct(used / win) + "</span> full &nbsp;&middot;&nbsp; <span class='n'>" + money(used * 5 / 1e6) +
            "</span> per request at $5 / M" +
            (used / win > 0.5 ? " &mdash; and past about half the window, accuracy on facts buried in the middle starts falling long before anything overflows."
                              : " &mdash; comfortable. Note that all of it is re-sent and re-charged on every single turn."));
      }
    };
  });

  /* ==================================================================
     6. Prompt caching
     ==================================================================
     Caching a prompt prefix is the cheapest large win in this whole field and
     the easiest to throw away: one volatile token near the front and every
     byte after it is recomputed. The figure runs six requests and prices them
     both ways. */

  reg("cache", function (api) {
    var order = "bad";
    var body = el("div");
    var k = knobs(api);
    api.stage.appendChild(body);
    k.sw("Prompt layout", [["bad", "Timestamp first"], ["good", "Stable prefix first"]], order,
         function (v) { order = v; api.rebuild(); });
    api.speed = 620;

    var BASE = 5 / 1e6, WRITE = 1.25, READ = 0.1;   /* $5 / M in, written at 1.25x, read at 0.1x */

    return {
      frames: function () {
        var F = [], prev = null, spentC = 0, spentP = 0, i;
        for (i = 0; i < 6; i++) {
          var blocks = order === "bad"
            ? [["Timestamp", 25, 1], ["System", 900, 0], ["Tools", 2200, 0],
               ["Retrieved docs", 5800, 0], ["History", i * 340, 1], ["Question", 60, 1]]
            : [["System", 900, 0], ["Tools", 2200, 0], ["Retrieved docs", 5800, 0],
               ["History", i * 340, 1], ["Timestamp", 25, 1], ["Question", 60, 1]];
          /* the cached prefix is the longest run of blocks byte-identical to
             the previous request -- which is exactly how the real thing works */
          var cached = 0, j;
          if (prev) {
            for (j = 0; j < blocks.length; j++) {
              if (prev[j] && prev[j][0] === blocks[j][0] && prev[j][1] === blocks[j][1]) cached += blocks[j][1];
              else break;
            }
          }
          var total = blocks.reduce(function (a, b) { return a + b[1]; }, 0);
          var fresh = total - cached;
          var cost = cached * BASE * READ + fresh * BASE * (i === 0 ? WRITE : 1);
          spentC += cost;
          spentP += total * BASE;
          F.push({ i: i, blocks: blocks, cached: cached, total: total, cost: cost,
                   spentC: spentC, spentP: spentP });
          prev = blocks;
        }
        return F;
      },
      start: function (F) { return F.length - 1; },
      render: function (f, i, total) {
        var rows = [], seen = 0;
        f.blocks.forEach(function (b) {
          var cachedHere = Math.max(0, Math.min(b[1], f.cached - seen));
          seen += b[1];
          var w = 100 * b[1] / f.total;
          rows.push("<i title='" + b[0] + "' style='width:" + w.toFixed(2) +
            "%;background:" + (cachedHere >= b[1] && b[1] > 0 ? "var(--l1)" :
              cachedHere > 0 ? "var(--l2)" : "var(--accent)") + "'></i>");
        });
        var labels = f.blocks.map(function (b) {
          return "<span>" + b[0] + " <b>" + commas(b[1]) + "</b></span>";
        });
        body.innerHTML = "<div class='stack'>" + rows.join("") + "</div>" +
          "<div class='stack-key'><span><i style='background:var(--l1)'></i>Read from cache</span>" +
          "<span><i style='background:var(--accent)'></i>Sent and processed again</span></div>" +
          "<div class='stack-key'>" + labels.join("") + "</div>";
        api.say("Request <span class='n'>" + (f.i + 1) + "</span> of 6 &nbsp;&middot;&nbsp; cached prefix <span class='n'>" +
          commas(f.cached) + "</span> of " + commas(f.total) + " tokens (<span class='n'>" +
          pct(f.cached / f.total) + "</span>) &nbsp;&middot;&nbsp; spent so far <span class='n'>" +
          money(f.spentC) + "</span> against <span class='n'>" + money(f.spentP) +
          "</span> with no cache" +
          (order === "bad" ? " &mdash; the timestamp at the front changes every request, so the prefix never matches and nothing is ever reused."
                           : " &mdash; everything stable sits at the front, so only the tail is new."));
      }
    };
  });
"""


D4 = r"""

  /* ==================================================================
     7. Chunking
     ==================================================================
     Retrieval can only ever return a chunk, so the chunk boundary decides what
     an answer is allowed to contain. Slide the size down far enough and the
     sentence that answers the question is cut in half; no amount of clever
     ranking recovers from that. */

  var DOC =
    "Returns and refunds\n\n" +
    "Any item bought from the online store can be sent back within thirty days of delivery, " +
    "provided it is unused and in its original packaging. A return is started from the orders " +
    "page and the label is generated automatically.\n\n" +
    "Once the warehouse has scanned the parcel an inspection is scheduled. Inspection normally " +
    "completes on the same working day, and you are emailed either an approval or a rejection " +
    "with the reason for it.\n\n" +
    "Refunds are issued within 14 business days of approval, to the original payment method.\n\n" +
    "Items marked final sale, gift cards and anything personalised are excluded. Faulty goods " +
    "are covered separately by the statutory warranty, which runs for two years from delivery.\n\n" +
    "For an order placed through a reseller, contact the reseller directly. Support cannot look " +
    "up an order it did not take payment for.";
  var ANSWER = "Refunds are issued within 14 business days of approval, to the original payment method.";
  var AT = DOC.indexOf(ANSWER), AEND = AT + ANSWER.length;

  reg("chunk", function (api) {
    var strategy = "lap", size = 260, lap = 60;
    var body = el("div", "docv");
    var k = knobs(api);
    api.stage.appendChild(body);
    k.sw("Strategy", [["fix", "Fixed"], ["lap", "Overlap"], ["para", "Paragraph"]], strategy,
         function (v) { strategy = v; api.rebuild(); });
    k.range("Chunk size", 80, 700, size, 20, function (v) { return v + " chars"; },
            function (v) { size = v; api.rebuild(); });
    k.range("Overlap", 0, 200, lap, 10, function (v) { return v + " chars"; },
            function (v) { lap = v; api.rebuild(); });

    function ranges() {
      var out = [], i;
      if (strategy === "para") {
        var paras = [], last = 0, m, re = /\n\n/g;
        while ((m = re.exec(DOC))) { paras.push([last, m.index]); last = m.index + 2; }
        paras.push([last, DOC.length]);
        var cur = null;
        paras.forEach(function (r) {
          if (cur && r[1] - cur[0] <= size) cur[1] = r[1];
          else { cur = [r[0], r[1]]; out.push(cur); }
        });
        return out;
      }
      var step = strategy === "lap" ? Math.max(20, size - lap) : size;
      for (i = 0; i < DOC.length; i += step) out.push([i, Math.min(DOC.length, i + size)]);
      return out;
    }

    /* the answer sentence gets underlined wherever it falls, which may be
       inside two different chunks at once */
    function paint(a, b) {
      var t = DOC.slice(a, b), lo = Math.max(a, AT), hi = Math.min(b, AEND), out;
      if (lo >= hi) out = esc(t);
      else out = esc(DOC.slice(a, lo)) + "<span class='hit'>" + esc(DOC.slice(lo, hi)) +
                 "</span>" + esc(DOC.slice(hi, b));
      return out.replace(/\n/g, "<br>");
    }

    return {
      render: function () {
        var ch = ranges(), cuts = { 0: 1 }, i;
        ch.forEach(function (c) { cuts[c[0]] = 1; cuts[c[1]] = 1; });
        cuts[DOC.length] = 1;
        var pts = Object.keys(cuts).map(Number).sort(function (a, b) { return a - b; });
        /* A point is a hard cut only if no chunk spans across it. With overlap
           on, most interval edges are a chunk *starting* while another still
           runs, and marking those as cuts made the figure claim the text was
           severed when a chunk still held it whole. */
        function hard(p) {
          if (p <= 0 || p >= DOC.length) return false;
          for (var q = 0; q < ch.length; q++) if (ch[q][0] < p && ch[q][1] > p) return false;
          return true;
        }
        var out = [];
        for (i = 0; i + 1 < pts.length; i++) {
          var a = pts[i], b = pts[i + 1];
          var cover = [];
          ch.forEach(function (c, j) { if (c[0] <= a && c[1] >= b) cover.push(j); });
          if (!cover.length) continue;
          if (hard(a)) out.push("<span class='split' title='chunk boundary'></span>");
          var cls = cover.length > 1 ? "ck lap" : "ck" + (cover[0] % 2 ? " alt" : "");
          out.push("<span class='" + cls + "'>" + paint(a, b) + "</span>");
        }
        body.innerHTML = out.join("");

        var whole = -1;
        ch.forEach(function (c, j) { if (whole < 0 && c[0] <= AT && c[1] >= AEND) whole = j; });
        var mean = ch.reduce(function (s, c) { return s + (c[1] - c[0]); }, 0) / ch.length;
        api.say("Question: <b>how long do refunds take?</b> &nbsp;&middot;&nbsp; <span class='n'>" +
          ch.length + "</span> chunks, mean <span class='n'>" + Math.round(mean) +
          "</span> characters (about <span class='n'>" + Math.round(mean / 4) + "</span> tokens) &nbsp;&middot;&nbsp; " +
          (whole >= 0
            ? "chunk <span class='n'>" + (whole + 1) + "</span> holds the answering sentence whole, so retrieval can return an answer."
            : "<b>the answering sentence is cut in half.</b> No chunk contains it, so no ranking, reranking or bigger model recovers the answer &mdash; the failure happened at index time."));
      }
    };
  });

  /* ==================================================================
     8. Approximate nearest neighbours
     ==================================================================
     Exact search reads every vector. An index instead builds a graph with a
     few long-range links, drops into it at one point, and walks downhill --
     touching a few dozen vectors instead of every one. The knob that matters
     is how many candidates it keeps in flight: that is the whole recall-versus
     -latency trade, and it is the same knob in every vector database. */

  function lcg(seed) {
    return function () { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
  }
  var PTS = (function () {
    var r = lcg(7), out = [], i, c;
    var centres = [[70, 70], [250, 60], [160, 150], [60, 210], [265, 205]];
    for (i = 0; i < 120; i++) {
      c = centres[i % centres.length];
      out.push({ x: c[0] + (r() + r() + r() - 1.5) * 52, y: c[1] + (r() + r() + r() - 1.5) * 44 });
    }
    return out;
  })();
  var QUERY = { x: 168, y: 140 };
  function d2(a, b) { var dx = a.x - b.x, dy = a.y - b.y; return dx * dx + dy * dy; }

  reg("ann", function (api) {
    var ef = 8, links = 4;
    var body = el("div");
    var k = knobs(api);
    api.stage.appendChild(body);
    k.range("Candidates kept (ef)", 1, 24, ef, 1, function (v) { return String(v); },
            function (v) { ef = v; api.rebuild(); });
    k.range("Links per vector", 2, 8, links, 1, function (v) { return String(v); },
            function (v) { links = v; api.rebuild(); });
    api.speed = 240;

    var trace = null;
    var EXACT = PTS.map(function (p, i) { return { i: i, d: d2(p, QUERY) }; })
      .sort(function (a, b) { return a.d - b.d; }).slice(0, 10).map(function (o) { return o.i; });

    function graph() {
      var r = lcg(19), nb = [], i, j;
      for (i = 0; i < PTS.length; i++) {
        var near = PTS.map(function (p, j2) { return { j: j2, d: d2(p, PTS[i]) }; })
          .filter(function (o) { return o.j !== i; })
          .sort(function (a, b) { return a.d - b.d; }).slice(0, links).map(function (o) { return o.j; });
        near.push(Math.floor(r() * PTS.length));       /* one long-range link: the small world */
        nb.push(near);
      }
      return nb;
    }

    return {
      frames: function () {
        var nb = graph(), visited = {}, cand = [{ i: 0, d: d2(PTS[0], QUERY) }], res = [], F = [];
        visited[0] = 1;
        while (cand.length) {
          cand.sort(function (a, b) { return a.d - b.d; });
          var c = cand.shift();
          if (res.length >= ef && c.d > res[res.length - 1].d) break;
          res.push(c);
          res.sort(function (a, b) { return a.d - b.d; });
          if (res.length > ef) res.pop();
          var added = [];
          nb[c.i].forEach(function (n) {
            if (visited[n]) return;
            visited[n] = 1; added.push(n);
            cand.push({ i: n, d: d2(PTS[n], QUERY) });
          });
          F.push({ cur: c.i, added: added, res: res.map(function (o) { return o.i; }),
                   touched: Object.keys(visited).length });
        }
        trace = F;
        return F;
      },
      start: function (F) { return F.length - 1; },
      render: function (f, i) {
        var seen = {}, j, s;
        for (j = 0; j <= i && trace; j++) {
          seen[trace[j].cur] = 1;
          trace[j].added.forEach(function (n) { seen[n] = 1; });
        }
        var inRes = {};
        f.res.forEach(function (n) { inRes[n] = 1; });
        var p = [], W = 340, H = 275;
        for (j = 0; j <= i && trace; j++) {
          if (j === 0) continue;
          var a = PTS[trace[j - 1].cur], b = PTS[trace[j].cur];
          p.push("<line class='edge on' x1='" + a.x.toFixed(1) + "' y1='" + a.y.toFixed(1) +
                 "' x2='" + b.x.toFixed(1) + "' y2='" + b.y.toFixed(1) + "'/>");
        }
        PTS.forEach(function (pt, j2) {
          var cls = inRes[j2] ? "node ok" : j2 === f.cur ? "node hot" : seen[j2] ? "node on" : "node";
          p.push("<g class='" + cls + "'><circle cx='" + pt.x.toFixed(1) + "' cy='" + pt.y.toFixed(1) +
                 "' r='" + (inRes[j2] || j2 === f.cur ? 5 : 3.2) + "'/></g>");
        });
        p.push("<path class='edge on' d='M" + (QUERY.x - 7) + " " + (QUERY.y - 7) + "l14 14M" +
               (QUERY.x + 7) + " " + (QUERY.y - 7) + "l-14 14' stroke-width='2.4'/>");
        body.innerHTML = "<svg viewBox='0 0 " + W + " " + H +
          "' role='img' aria-label='A graph index being walked towards the query'>" + p.join("") + "</svg>";

        var hit = f.res.filter(function (n) { return EXACT.indexOf(n) >= 0; }).length;
        api.say("Touched <span class='n'>" + f.touched + "</span> of " + PTS.length +
          " vectors &nbsp;&middot;&nbsp; holding <span class='n'>" + f.res.length +
          "</span> candidates &nbsp;&middot;&nbsp; recall@10 so far <span class='n'>" +
          pct(hit / 10) + "</span>" +
          (i === (trace ? trace.length - 1 : 0)
            ? (hit === 10 ? " &mdash; the walk found the true ten while reading a fraction of the set. That fraction is the entire reason vector databases exist."
                          : " &mdash; it missed " + (10 - hit) + ". Raise ef and it will find them, and take longer. There is no setting that gives you both.")
            : ""));
      }
    };
  });
"""


D5 = r"""

  /* ==================================================================
     9. Hybrid retrieval and fusion
     ==================================================================
     Two retrievers fail in opposite directions. Keyword search cannot match a
     paraphrase; vector search cannot match an identifier it has never seen as
     a word. Fusing them by *rank* rather than by score is the standard fix,
     because a BM25 score and a cosine are not on the same scale and averaging
     them is arithmetic on incompatible units. */

  var DOCS = [
    ["Invoice INV-90412: terms and payment schedule", 1, 8, 0.98],
    ["How long before the money comes back to me", 8, 1, 0.94],
    ["Refund processing times by payment method", 4, 2, 0.90],
    ["Shipping and delivery estimates", 6, 5, 0.10],
    ["Invoice numbering scheme explained", 2, 9, 0.28],
    ["Statutory warranty on faulty goods", 9, 4, 0.16],
    ["Reseller orders and who to contact", 7, 7, 0.08],
    ["Payment methods we accept", 3, 6, 0.34],
    ["Cancelling an order before dispatch", 5, 3, 0.22],
    ["Gift cards are non-refundable", 10, 10, 0.20]
  ];

  reg("fuse", function (api) {
    var kk = 60, rerank = false;
    var body = el("div", "trio");
    var k = knobs(api);
    api.stage.appendChild(body);
    k.range("RRF constant k", 1, 100, kk, 1, function (v) { return String(v); },
            function (v) { kk = v; api.rebuild(); });
    k.sw("Cross-encoder", [["off", "Off"], ["on", "Rerank top 6"]], "off",
         function (v) { rerank = v === "on"; api.rebuild(); });

    function list(title, order) {
      var out = ["<h6>" + title + "</h6><div class='rows'>"];
      order.forEach(function (d, i) {
        var gold = d[3] > 0.85;
        out.push("<div class='row'><span class='lab'>" + (i + 1) + "</span><span class='cell " +
          (gold ? "hit" : "") + "' style='min-width:0;flex:1 1 auto;justify-content:flex-start;" +
          "padding:0 7px;font-size:0.68rem'>" + esc(d[0]) + "</span></div>");
      });
      return out.join("") + "</div>";
    }

    return {
      render: function () {
        var bm = DOCS.slice().sort(function (a, b) { return a[1] - b[1]; });
        var de = DOCS.slice().sort(function (a, b) { return a[2] - b[2]; });
        var fused = DOCS.map(function (d) {
          return { d: d, s: 1 / (kk + d[1]) + 1 / (kk + d[2]) };
        }).sort(function (a, b) { return b.s - a.s; }).map(function (o) { return o.d; });
        if (rerank) {
          var head = fused.slice(0, 6).sort(function (a, b) { return b[3] - a[3]; });
          fused = head.concat(fused.slice(6));
        }
        body.innerHTML = "<div>" + list("Keyword &middot; BM25", bm) + "</div>" +
                         "<div>" + list("Vector &middot; cosine", de) + "</div>" +
                         "<div>" + list(rerank ? "Fused, then reranked" : "Fused &middot; RRF", fused) + "</div>";
        var pos = function (arr, name) {
          for (var i = 0; i < arr.length; i++) if (arr[i][0] === name) return i + 1;
          return 0;
        };
        var idDoc = DOCS[0][0], paraDoc = DOCS[1][0];
        api.say("Query: <b>INV-90412 refund timing</b> &nbsp;&middot;&nbsp; the invoice number ranks <span class='n'>" +
          pos(bm, idDoc) + "</span> on keywords but <span class='n'>" + pos(de, idDoc) +
          "</span> on vectors; the paraphrase ranks <span class='n'>" + pos(de, paraDoc) +
          "</span> on vectors but <span class='n'>" + pos(bm, paraDoc) +
          "</span> on keywords. Fused they sit at <span class='n'>" + pos(fused, idDoc) + "</span> and <span class='n'>" +
          pos(fused, paraDoc) + "</span>." +
          (rerank ? " The cross-encoder reads each candidate <em>with</em> the query, which is why it can reorder what the fusion could only guess at &mdash; and why it costs a model call per candidate."
                  : " Reciprocal rank fusion never looks at a score, only a position, which is what makes it safe to combine retrievers you cannot calibrate against each other."));
      }
    };
  });

  /* ==================================================================
     10. The agent loop
     ==================================================================
     An agent is a loop, not a model: call the model, it asks for a tool, run
     the tool, append the result, call the model again. Two things surprise
     people the first time they see it laid out. The message array only ever
     grows, and every model call re-reads all of it -- so a ten-step task is
     not ten times the cost of a one-step task, it is closer to fifty. And a
     tool error is not an exception; it is just another message. */

  var STEPS = [
    ["sys", "System", "You are an accounts assistant. Tools: list_invoices, get_terms, search_customers.", 620],
    ["user", "User", "Which of my open invoices are overdue, and by how much?", 28],
    ["model", "Model &rarr; tool_use", "list_invoices(status=&quot;open&quot;)", 46],
    ["tool", "Tool result", "12 invoices, with amounts and due dates", 1840],
    ["model", "Model &rarr; tool_use", "get_terms(customer=&quot;ACME&quot;)", 38],
    ["err", "Tool result &middot; error", "404 unknown customer &quot;ACME&quot; &mdash; not an exception, just the next message", 26],
    ["model", "Model &rarr; tool_use", "search_customers(q=&quot;ACME&quot;)", 34],
    ["tool", "Tool result", "3 matches: ACME Ltd, ACME Holdings, Acme GmbH", 180],
    ["model", "Model &rarr; tool_use", "get_terms(customer_id=&quot;cus_81f2&quot;)", 42],
    ["tool", "Tool result", "net-30, no grace period", 90],
    ["model", "Model &rarr; answer", "Four invoices are overdue, by 3 to 41 days, totalling &pound;18,400.", 210]
  ];

  reg("agent", function (api) {
    var box = el("div", "msgs");
    api.stage.appendChild(box);
    api.speed = 700;

    return {
      frames: function () {
        var F = [], ctx = 0, billed = 0, calls = 0, i;
        for (i = 0; i < STEPS.length; i++) {
          ctx += STEPS[i][3];
          /* a model turn re-sends everything before it and is billed for the
             whole array, every time */
          if (STEPS[i][0] === "model") { calls++; billed += ctx; }
          F.push({ i: i, ctx: ctx, billed: billed, calls: calls });
        }
        return F;
      },
      start: function (F) { return Math.min(5, F.length - 1); },
      render: function (f, i) {
        var out = [], j;
        for (j = 0; j <= i; j++) {
          var s = STEPS[j];
          out.push("<div class='msg " + s[0] + (j === i ? " now" : "") + "'><span class='r'>" + s[1] +
            " &middot; " + commas(s[3]) + " tokens</span>" + s[2] + "</div>");
        }
        box.innerHTML = out.join("");
        api.say("Step <span class='n'>" + (f.i + 1) + "</span> of " + STEPS.length +
          " &nbsp;&middot;&nbsp; context <span class='n'>" + commas(f.ctx) +
          "</span> tokens &nbsp;&middot;&nbsp; <span class='n'>" + f.calls +
          "</span> model calls &nbsp;&middot;&nbsp; input tokens billed <span class='n'>" +
          commas(f.billed) + "</span> (" + money(f.billed * 5 / 1e6) + " at $5 / M)" +
          (f.i === STEPS.length - 1
            ? " &mdash; six model calls over a context that ended at " + commas(f.ctx) +
              " tokens billed " + commas(f.billed) + ". Halving the size of that tool result is worth more than any prompt tweak."
            : ""));
      }
    };
  });

  /* ==================================================================
     11. A threshold, and the four numbers it decides
     ==================================================================
     Every classifier -- a safety filter, a router, a judge reduced to pass or
     fail -- is a score plus a line drawn through it. Moving the line trades
     precision against recall and cannot improve both. The prevalence knob is
     the one that catches people out: at a low base rate, a model that never
     fires at all still scores extremely well on accuracy. */

  reg("threshold", function (api) {
    var cut = 9.5, prev = 0.12, sep = 6;
    var wrap = el("div", "growth"), left = el("div"), right = el("div");
    wrap.appendChild(left); wrap.appendChild(right);
    var k = knobs(api);
    api.stage.appendChild(wrap);
    k.range("Threshold", 0, 20, cut, 0.5, function (v) { return v.toFixed(1); },
            function (v) { cut = v; api.rebuild(); });
    k.range("Positives in the data", 0.01, 0.5, prev, 0.01, function (v) { return pct(v); },
            function (v) { prev = v; api.rebuild(); });
    k.range("How separable", 2, 10, sep, 0.5, function (v) { return v.toFixed(1); },
            function (v) { sep = v; api.rebuild(); });

    var N = 4000, BINS = 20;
    function bell(mu, sd) {
      var out = [], i, s = 0;
      for (i = 0; i < BINS; i++) {
        var z = (i + 0.5 - mu) / sd;
        var v = Math.exp(-0.5 * z * z);
        out.push(v); s += v;
      }
      return out.map(function (v) { return v / s; });
    }

    return {
      render: function () {
        var np = Math.round(N * prev), nn = N - np;
        var pos = bell(10 + sep / 2, 2.6).map(function (v) { return v * np; });
        var neg = bell(10 - sep / 2, 2.6).map(function (v) { return v * nn; });
        var tp = 0, fp = 0, fn = 0, tn = 0, i;
        for (i = 0; i < BINS; i++) {
          if (i + 0.5 >= cut) { tp += pos[i]; fp += neg[i]; }
          else { fn += pos[i]; tn += neg[i]; }
        }
        tp = Math.round(tp); fp = Math.round(fp); fn = Math.round(fn); tn = Math.round(tn);
        var peak = 0;
        for (i = 0; i < BINS; i++) peak = Math.max(peak, pos[i] + neg[i]);
        var bars = [];
        for (i = 0; i < BINS; i++) {
          var hn = 100 * neg[i] / peak, hp = 100 * pos[i] / peak;
          bars.push("<div class='h'><i class='neg' style='height:" + hn.toFixed(1) +
            "%'></i><i class='pos' style='height:" + hp.toFixed(1) + "%;bottom:" + hn.toFixed(1) + "%'></i></div>");
        }
        left.innerHTML = "<div class='hist'>" + bars.join("") + "<span class='cut' style='left:" +
          (100 * cut / BINS).toFixed(2) + "%'></span></div>" +
          "<div class='stack-key'><span><i style='background:var(--l2)'></i>Should fire</span>" +
          "<span><i style='background:color-mix(in srgb,var(--ink-faint) 45%,var(--surface))'></i>Should not</span>" +
          "<span><i style='background:var(--l3)'></i>Threshold</span></div>";
        right.innerHTML = "<table class='cm'><tr><th></th><th>Fired</th><th>Did not</th></tr>" +
          "<tr><th>Should</th><td class='tp'>" + commas(tp) + "<small>true positive</small></td>" +
          "<td class='fn'>" + commas(fn) + "<small>missed</small></td></tr>" +
          "<tr><th>Should not</th><td class='fp'>" + commas(fp) + "<small>false alarm</small></td>" +
          "<td class='tn'>" + commas(tn) + "<small>true negative</small></td></tr></table>";

        var P = tp / (tp + fp || 1), R = tp / (tp + fn || 1), F1 = 2 * P * R / (P + R || 1);
        var acc = (tp + tn) / N, base = Math.max(prev, 1 - prev);
        api.say("Precision <span class='n'>" + pct(P) + "</span> &nbsp;&middot;&nbsp; recall <span class='n'>" +
          pct(R) + "</span> &nbsp;&middot;&nbsp; F1 <span class='n'>" + round(F1, 3) +
          "</span> &nbsp;&middot;&nbsp; accuracy <span class='n'>" + pct(acc) + "</span>" +
          (prev <= 0.1
            ? " &mdash; but a model that never fires at all scores <b>" + pct(1 - prev) +
              "</b> accuracy on this data. At a low base rate, accuracy is not a metric, it is a disguise."
            : R < 0.5 ? " &mdash; half the cases that should fire do not. If those are safety violations, this threshold is the wrong one whatever precision says."
                      : ""));
      }
    };
  });
"""


D6 = r"""

  /* ==================================================================
     12. Low-rank adaptation
     ==================================================================
     A weight matrix is d by d. LoRA freezes it and learns two thin matrices
     beside it, d by r and r by d, whose product has the same shape. When r is
     sixteen and d is four thousand, that is a third of a percent of the
     parameters -- and since the optimizer state is the real memory cost of
     training, it is the difference between eight cards and one. */

  var BASES = [
    ["8", "Llama-class 8B"], ["13", "13B"], ["70", "Llama-class 70B"]
  ];
  var BASE_SHAPE = { "8": { p: 8.0e9, L: 32, d: 4096 },
                     "13": { p: 13.0e9, L: 40, d: 5120 },
                     "70": { p: 70.6e9, L: 80, d: 8192 } };

  reg("lora", function (api) {
    var base = "8", r = 16, mods = "attn", prec = "bf16";
    var wrap = el("div", "growth"), left = el("div"), right = el("div");
    wrap.appendChild(left); wrap.appendChild(right);
    var k = knobs(api);
    api.stage.appendChild(wrap);
    k.pick("Base model", BASES, base, function (v) { base = v; api.rebuild(); });
    k.range("Rank r", 1, 128, r, 1, function (v) { return String(v); },
            function (v) { r = v; api.rebuild(); });
    k.sw("Adapted", [["attn", "Attention"], ["all", "All linear"]], mods,
         function (v) { mods = v; api.rebuild(); });
    k.sw("Frozen base held as", [["bf16", "bf16"], ["nf4", "4-bit"]], prec,
         function (v) { prec = v; api.rebuild(); });

    return {
      render: function () {
        var s = BASE_SHAPE[base];
        var nMat = mods === "attn" ? 4 : 7;          /* q,k,v,o -- plus the MLP's three */
        var train = s.L * nMat * 2 * s.d * r;
        /* Adam keeps two moments plus a gradient, in fp32: 12 bytes a trainable
           parameter, on top of 4 for the parameter itself. */
        var full = s.p * 16;
        var loraMem = s.p * (prec === "bf16" ? 2 : 0.5) + train * 16;
        var W = 320, H = 250, side = 150, x0 = 22, y0 = 46;
        /* drawn at 26x scale and capped, or r=1 would be a hairline: the
           caption says so, and the honest ratio is in the table */
        var rr = Math.min(58, Math.max(3, side * r / s.d * 26));
        var p = [];
        p.push("<g class='node'><rect x='" + x0 + "' y='" + y0 + "' width='" + side + "' height='" + side + "'/>" +
          "<text x='" + (x0 + side / 2) + "' y='" + (y0 + side / 2 + 4) + "' text-anchor='middle'>W frozen</text></g>");
        p.push("<text x='" + (x0 + side / 2) + "' y='" + (y0 - 14) + "' text-anchor='middle' fill='currentColor'>d = " +
          commas(s.d) + "</text>");
        p.push("<text x='" + (x0 + side + 26) + "' y='" + (y0 + side / 2) + "' fill='currentColor'>+</text>");
        var bx = x0 + side + 48;
        p.push("<g class='node on'><rect x='" + bx + "' y='" + y0 + "' width='" + rr.toFixed(1) + "' height='" + side + "'/></g>");
        p.push("<text x='" + (bx + rr / 2) + "' y='" + (y0 + side + 16) + "' text-anchor='middle' fill='currentColor'>B</text>");
        p.push("<g class='node ok'><rect x='" + bx + "' y='" + (y0 + side + 26) + "' width='" + side + "' height='" + rr.toFixed(1) + "'/></g>");
        p.push("<text x='" + (bx + side + 12) + "' y='" + (y0 + side + 30 + rr / 2) + "' fill='currentColor'>A &middot; r = " + r + "</text>");
        left.innerHTML = "<svg viewBox='0 0 " + W + " " + H +
          "' role='img' aria-label='A frozen weight matrix beside its two thin adapters'>" + p.join("") + "</svg>";

        right.innerHTML = "<table class='gtab'><tr><th>Approach</th><th>trainable</th><th>memory</th></tr>" +
          "<tr class='hot'><td>Full fine-tune</td><td>" + big(s.p) + "</td><td>" + gb(full) + "</td></tr>" +
          "<tr class='fine'><td>LoRA r=" + r + "</td><td>" + big(train) + "</td><td>" + gb(loraMem) + "</td></tr>" +
          "<tr><td>Share of weights</td><td>" + round(100 * train / s.p, 3) + "%</td><td>&mdash;</td></tr>" +
          "<tr><td>Adapter on disk</td><td>&mdash;</td><td>" + gb(train * 2) + "</td></tr></table>";
        api.say("<span class='n'>" + big(train) + "</span> trainable parameters, <span class='n'>" +
          round(100 * train / s.p, 3) + "%</span> of the model &nbsp;&middot;&nbsp; training memory <span class='n'>" +
          gb(loraMem) + "</span> against <span class='n'>" + gb(full) +
          "</span> for a full fine-tune &nbsp;&middot;&nbsp; the adapter ships as a <span class='n'>" + gb(train * 2) +
          "</span> file you can swap per customer without redeploying the model." +
          (r >= 64 ? " At this rank you are close to the point where a full fine-tune is simpler to reason about." : ""));
      }
    };
  });

  /* ==================================================================
     13. What has to fit on the card
     ==================================================================
     Three things share the memory: the weights, the KV cache, and everything
     transient. Only the first is a constant. The second is the one that
     decides how many users you can serve at once, and it is linear in both
     context length and concurrency -- which is why the shape of the attention
     (how many key/value heads there are) is a serving decision, not a research
     one. The formula is printed under the figure; the knobs just evaluate it. */

  var MODELS = [
    ["8b", "Llama 3.1 8B"], ["70b", "Llama 3.1 70B"], ["405b", "Llama 3.1 405B"],
    ["7b", "Mistral 7B"], ["mha", "8B, but with MHA"]
  ];
  var SHAPE = {
    "8b": { p: 8.03e9, L: 32, kv: 8, hd: 128 },
    "70b": { p: 70.6e9, L: 80, kv: 8, hd: 128 },
    "405b": { p: 405e9, L: 126, kv: 8, hd: 128 },
    "7b": { p: 7.24e9, L: 32, kv: 8, hd: 128 },
    "mha": { p: 8.03e9, L: 32, kv: 32, hd: 128 }
  };
  var CARDS = [["80", "1 x 80 GB"], ["160", "2 x 80 GB"], ["320", "4 x 80 GB"], ["640", "8 x 80 GB"]];

  reg("vram", function (api) {
    var model = "8b", bits = 2, ctx = 8192, batch = 32, card = "80";
    var body = el("div");
    var k = knobs(api);
    api.stage.appendChild(body);
    k.pick("Model", MODELS, model, function (v) { model = v; api.rebuild(); });
    k.sw("Weights", [["2", "bf16"], ["1", "fp8"], ["0.5", "4-bit"]], "2",
         function (v) { bits = +v; api.rebuild(); });
    k.range("Context per sequence", 1024, 131072, ctx, 1024, function (v) { return big(v) + " tok"; },
            function (v) { ctx = v; api.rebuild(); });
    k.range("Concurrent sequences", 1, 256, batch, 1, function (v) { return String(v); },
            function (v) { batch = v; api.rebuild(); });
    k.pick("Hardware", CARDS, card, function (v) { card = v; api.rebuild(); });

    return {
      render: function () {
        var s = SHAPE[model], cap = +card * 1073741824;
        var weights = s.p * bits;
        var perTok = 2 * s.L * s.kv * s.hd * 2;      /* K and V, fp16, per token per sequence */
        var kv = perTok * ctx * batch;
        var slack = weights * 0.06 + batch * 40e6;   /* CUDA graphs, activations, fragmentation */
        var total = weights + kv + slack;
        var scale = Math.max(total, cap);
        var row = function (name, v, cls) {
          return "<div class='m'><span>" + name + "</span><div class='stack'><i class='" + cls +
            "' style='width:" + (100 * v / scale).toFixed(2) + "%'></i></div></div>";
        };
        body.innerHTML = "<div class='mbar'>" +
          row("Weights", weights, "s1") + row("KV cache", kv, "s2") +
          row("Everything else", slack, "s5") +
          row("Card capacity", cap, total > cap ? "over" : "s3") + "</div>" +
          "<div class='stack-key'><span>KV per token <b>" + gb(perTok) + "</b></span>" +
          "<span>2 &times; layers &times; kv-heads &times; head-dim &times; 2 bytes = 2 &times; " + s.L +
          " &times; " + s.kv + " &times; " + s.hd + " &times; 2</span></div>";
        var room = cap - weights - slack;
        var maxSeq = Math.max(0, Math.floor(room / (perTok * ctx)));
        api.say("Weights <span class='n'>" + gb(weights) + "</span> + KV <span class='n'>" + gb(kv) +
          "</span> + slack <span class='n'>" + gb(slack) + "</span> = <span class='n'>" + gb(total) +
          "</span> of " + gb(cap) + (total > cap
            ? " &mdash; <b>it does not fit.</b> Shorten the context, serve fewer at once, quantise the weights, or add a card."
            : " &mdash; fits, with room for <span class='n'>" + commas(maxSeq) + "</span> sequences at this context length.") +
          (s.kv === 32 ? " This variant keeps a key/value head per query head, which is why its cache is four times the size of the grouped one for the same model."
                       : ""));
      }
    };
  });
"""


D7 = r"""

  /* ==================================================================
     14. How the GPU is shared
     ==================================================================
     Requests arrive at different times and finish at different times. A static
     batch has to wait for its slowest member before it can admit anyone new,
     so the fast requests sit finished in their slot doing nothing. Continuous
     batching makes the scheduling unit a single decode step: a slot frees the
     instant its sequence emits a stop token, and the next request is admitted
     on the very next step. That one change is most of what an inference server
     is for. */

  var REQS = [
    { at: 0, len: 6 }, { at: 0, len: 22 }, { at: 0, len: 4 }, { at: 1, len: 9 },
    { at: 3, len: 5 }, { at: 5, len: 14 }, { at: 8, len: 3 }, { at: 9, len: 7 }
  ];
  var SLOTS = 4, HORIZON = 46;

  reg("batching", function (api) {
    var mode = "cont";
    var body = el("div");
    var k = knobs(api);
    api.stage.appendChild(body);
    k.sw("Scheduler", [["static", "Static batch"], ["cont", "Continuous"]], mode,
         function (v) { mode = v; api.rebuild(); });
    api.speed = 130;

    var grid = null, finished = null, span = 0;

    /* Both schedulers are simulated the same way: one column per decode step,
       one lane per slot. The only difference is when a slot may be refilled. */
    function schedule() {
      var lanes = [], i, t;
      for (i = 0; i < SLOTS; i++) lanes.push([]);
      var queue = REQS.map(function (r, i2) { return { id: i2, at: r.at, left: r.len, started: -1 }; });
      var running = new Array(SLOTS).fill(null);
      var done = [];
      span = 0;
      for (t = 0; t < HORIZON; t++) {
        /* the one line that separates the two schedulers: a static batch may
           only take new work when every slot is free */
        var canAdmit = mode === "cont" || running.every(function (x) { return !x; });
        if (canAdmit) {
          for (i = 0; i < SLOTS; i++) {
            if (running[i]) continue;
            var next = queue.filter(function (q) { return q.at <= t && q.started < 0; })[0];
            if (!next) break;
            next.started = t;
            running[i] = next;
          }
        }
        for (i = 0; i < SLOTS; i++) {
          var r = running[i];
          if (!r) { lanes[i].push("idle"); continue; }
          if (r.spent) { lanes[i].push("held"); continue; }   /* finished, still reserved */
          lanes[i].push(r.started === t ? "pre" : "dec");
          r.left -= 1;
          if (r.left <= 0) {
            done.push({ id: r.id, at: t });
            if (mode === "cont") running[i] = null;
            else r.spent = true;
          }
        }
        if (mode !== "cont" && running.every(function (x) { return !x || x.spent; })) {
          for (i = 0; i < SLOTS; i++) running[i] = null;
        }
        if (done.length === REQS.length) { span = t + 1; break; }
      }
      if (!span) span = HORIZON;
      for (i = 0; i < SLOTS; i++) {
        for (t = 0; t < span; t++) if (lanes[i][t] === undefined) lanes[i][t] = "idle";
      }
      grid = lanes; finished = done;
      return span;
    }

    return {
      frames: function () {
        var n = schedule(), F = [], t;
        for (t = 0; t < n; t++) F.push(t);
        return F;
      },
      start: function (F) { return F.length - 1; },
      render: function (t, i, total) {
        var out = [], s, busy = 0, cells = 0;
        for (s = 0; s < SLOTS; s++) {
          var lane = ["<div class='lane'><span class='lab'>slot " + s + "</span>"];
          for (var x = 0; x <= t; x++) {
            var v = grid[s][x] || "idle";
            if (v === "pre" || v === "dec") busy++;
            cells++;   /* held and idle both count against utilisation */
            lane.push("<u class='" + v + (x === t ? " now" : "") + "'></u>");
          }
          lane.push("</div>");
          out.push(lane.join(""));
        }
        body.innerHTML = "<div class='tl'>" + out.join("") + "</div>" +
          "<div class='stack-key'><span><i style='background:var(--l3)'></i>Prefill</span>" +
          "<span><i style='background:var(--l2)'></i>Decode step</span>" +
          "<span><i style='background:var(--surface-2)'></i>Idle</span>" +
          "<span><i class='held'></i>Finished, slot still reserved</span></div>";
        var doneNow = finished.filter(function (d) { return d.at <= t; }).length;
        api.say("Step <span class='n'>" + t + "</span> &nbsp;&middot;&nbsp; finished <span class='n'>" +
          doneNow + "</span> of " + REQS.length + " &nbsp;&middot;&nbsp; GPU busy <span class='n'>" +
          pct(busy / (cells || 1)) + "</span> of its slot-steps" +
          (t === total - 1
            ? " &mdash; all eight through in <b>" + total + " steps</b> with " +
              (mode === "cont" ? "continuous batching. Switch to the static batch and watch the same work take longer while slots sit finished but reserved."
                               : "a static batch. Switch to continuous and the same eight requests finish sooner, on the same hardware, because a freed slot is refilled on the next step.")
            : ""));
      }
    };
  });

  /* ==================================================================
     15. What it costs
     ==================================================================
     The bill is four multiplications, and every lever an engineer has shows up
     in one of them. The two tiers here are Claude Opus 5 and Claude Haiku 4.5
     at their August 2026 list prices; check the current ones before quoting any
     of this in an interview, because prices move and the arithmetic does not. */

  reg("cost", function (api) {
    var rpd = 50000, tin = 4000, tout = 500, hit = 0, small = 0;
    var body = el("div");
    var k = knobs(api);
    api.stage.appendChild(body);
    k.range("Requests per day", 1000, 500000, rpd, 1000, function (v) { return big(v); },
            function (v) { rpd = v; api.rebuild(); });
    k.range("Input tokens each", 200, 30000, tin, 100, function (v) { return commas(v); },
            function (v) { tin = v; api.rebuild(); });
    k.range("Output tokens each", 50, 4000, tout, 50, function (v) { return commas(v); },
            function (v) { tout = v; api.rebuild(); });
    k.range("Prefix cached", 0, 0.95, hit, 0.05, function (v) { return pct(v); },
            function (v) { hit = v; api.rebuild(); });
    k.range("Sent to the small model", 0, 1, small, 0.05, function (v) { return pct(v); },
            function (v) { small = v; api.rebuild(); });

    var BIG_IN = 5 / 1e6, BIG_OUT = 25 / 1e6, SM_IN = 1 / 1e6, SM_OUT = 5 / 1e6, CACHE = 0.1;

    return {
      render: function () {
        var big_n = rpd * (1 - small), sm_n = rpd * small;
        var cachedIn = tin * hit, freshIn = tin - cachedIn;
        var cIn = (big_n * (freshIn * BIG_IN + cachedIn * BIG_IN * CACHE)) +
                  (sm_n * (freshIn * SM_IN + cachedIn * SM_IN * CACHE));
        var cOut = big_n * tout * BIG_OUT + sm_n * tout * SM_OUT;
        var day = cIn + cOut;
        var naive = rpd * (tin * BIG_IN + tout * BIG_OUT);
        var scale = Math.max(day, naive);
        var row = function (name, v, cls) {
          return "<div class='m'><span>" + name + "</span><div class='stack'><i class='" + cls +
            "' style='width:" + (100 * v / scale).toFixed(2) + "%'></i></div></div>";
        };
        body.innerHTML = "<div class='mbar'>" +
          row("Input", cIn, "s1") + row("Output", cOut, "s2") +
          row("Today's bill", day, "s3") +
          row("No cache, no routing", naive, "s4") + "</div>" +
          "<div class='stack-key'><span>Frontier <b>$5 / $25</b> per M in / out</span>" +
          "<span>Small <b>$1 / $5</b></span><span>Cached input read at <b>10%</b></span>" +
          "<span class='n'>August 2026 list prices</span></div>";
        api.say("<span class='n'>" + money(day) + "</span> a day &nbsp;&middot;&nbsp; <span class='n'>" +
          money(day * 30.4) + "</span> a month &nbsp;&middot;&nbsp; <span class='n'>" +
          money(day / (rpd || 1)) + "</span> per request &nbsp;&middot;&nbsp; against <span class='n'>" +
          money(naive * 30.4) + "</span> a month with everything on the frontier model and nothing cached" +
          (day < naive * 0.999 ? " &mdash; a saving of <b>" + pct(1 - day / naive) + "</b>, from two settings and no new model."
                               : " &mdash; try the two bottom sliders."));
      }
    };
  });
"""

JS = (demo_ui.PLAYER_JS + D0 + D1 + D2 + D3 + D4 + D5 + D6 + D7
      + demo_ui.BOOT_JS)
