# -*- coding: utf-8 -*-
"""The stages the AI engineering page draws into, plus its language switch.

The player, the chrome around a figure and the switch behaviour come from
demo_ui.py, shared with the algorithms page. What is here is the stages only
this page has: token chips, an attention matrix, probability distributions,
budget bars, a document with chunk boundaries, a message transcript, a
confusion matrix, and a scheduling timeline.

The switch offers Python, TypeScript and Go rather than the series' usual
Go/Python/Java, because those are the three languages this work is actually
written in: the model-side code is Python, the product around it is usually
TypeScript, and the service that has to survive production is often Go. It
therefore stores the choice under its own key -- a reader who picked Java on
the algorithms page would otherwise arrive here with no pane selected at all.
"""

import demo_ui

# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

# Tokens. The alternating tint is the whole point of the figure: it makes the
# boundaries visible without drawing a box around every fragment.
TOKS = """
/* tokens */
.toks{display:flex;flex-wrap:wrap;gap:2px;font-family:"IBM Plex Mono",monospace;font-size:0.82rem;
  line-height:1.5}
.tok{padding:2px 3px;border-bottom:2px solid var(--l2);background:color-mix(in srgb,var(--l2) 12%,var(--surface));
  white-space:pre;color:var(--ink)}
.tok.alt{border-bottom-color:var(--l1);background:color-mix(in srgb,var(--l1) 12%,var(--surface))}
.tok.sp{color:var(--ink-faint)}
.tok i{font-style:normal;font-size:0.62rem;color:var(--ink-faint);margin-left:3px;
  vertical-align:super;font-variant-numeric:tabular-nums}
.toks.plain .tok{border-bottom:none;background:transparent;padding:2px 0}
"""

# A weight matrix: attention, or any other n-by-n table of numbers where the
# value is carried by the fill rather than the digits.
MAT = """
/* weight matrix */
.mat{border-collapse:collapse;font-family:"IBM Plex Mono",monospace;font-size:0.66rem;
  font-variant-numeric:tabular-nums;width:auto;min-width:0}
.mat th{font-weight:400;color:var(--ink-faint);padding:2px 5px;background:transparent;
  font-size:0.66rem;letter-spacing:0;text-transform:none;white-space:nowrap}
.mat th.r{text-align:right}
.mat td{width:30px;height:24px;text-align:center;border:1px solid var(--line);
  color:var(--ink);background:var(--surface)}
.mat td.z{color:var(--ink-faint);background:var(--surface-2)}
.mat tr.on th{color:var(--l2);font-weight:600}
.mat tr.on td{border-color:var(--l2)}
.mat td.pk{outline:2px solid var(--l3);outline-offset:-2px}
"""

# A probability distribution, or any labelled set of magnitudes: label, bar,
# number. Horizontal because the labels are words.
DIST = """
/* distribution rows */
.dist{display:grid;gap:3px}
.dist .d{display:grid;grid-template-columns:11ch 1fr 7ch;gap:8px;align-items:center;
  font-family:"IBM Plex Mono",monospace;font-size:0.72rem}
.dist .d .t{color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dist .d .v{text-align:right;color:var(--ink-soft);font-variant-numeric:tabular-nums}
.dist .d .b{height:14px;background:var(--surface-2);position:relative}
.dist .d .b span{position:absolute;left:0;top:0;bottom:0;background:var(--l2);display:block}
.dist .d.cut .t,.dist .d.cut .v{color:var(--ink-faint)}
.dist .d.cut .b span{background:var(--ink-faint);opacity:0.4}
.dist .d.pick .b span{background:var(--l1)}
.dist .d.pick .t{color:var(--l1);font-weight:600}
"""

# A budget: one bar made of labelled segments, drawn against a capacity.
STACK = """
/* stacked budget bars */
.stack{display:flex;height:30px;border:1px solid var(--line);background:var(--surface-2);
  overflow:hidden}
.stack i{display:block;height:100%;font-style:normal}
.stack i.s1{background:var(--accent)} .stack i.s2{background:var(--l2)}
.stack i.s3{background:var(--l1)} .stack i.s4{background:var(--l3)}
.stack i.s5{background:var(--ink-faint)}
.stack i.over{background:repeating-linear-gradient(45deg,var(--l3),var(--l3) 4px,var(--surface) 4px,var(--surface) 8px)}
.stack-key{display:flex;flex-wrap:wrap;gap:4px 15px;margin-top:9px;
  font-family:"IBM Plex Mono",monospace;font-size:0.66rem;color:var(--ink-faint)}
.stack-key span{display:inline-flex;align-items:center;gap:6px}
.stack-key i{width:10px;height:10px;display:inline-block;font-style:normal;border:1px solid var(--line)}
.stack-key b{color:var(--ink-soft);font-weight:600;font-variant-numeric:tabular-nums}
.mbar{display:grid;gap:7px;margin-top:4px}
.mbar .m{display:grid;grid-template-columns:16ch 1fr;gap:9px;align-items:center;
  font-family:"IBM Plex Mono",monospace;font-size:0.7rem;color:var(--ink-faint)}
.mbar .m .stack{height:22px}
"""

# A document with the chunk boundaries drawn on it.
DOCV = """
/* chunked document */
.docv{font-size:0.8rem;line-height:1.75;color:var(--ink-soft);max-width:70ch}
.docv .ck{padding:0 1px;background:color-mix(in srgb,var(--l2) 8%,transparent)}
.docv .ck.alt{background:color-mix(in srgb,var(--l1) 8%,transparent)}
.docv .ck.lap{background:color-mix(in srgb,var(--l3) 18%,transparent)}
.docv .hit{box-shadow:inset 0 -2px 0 var(--l3);color:var(--ink);font-weight:600}
/* Only a *hard* boundary gets a marker -- a point no chunk spans. An interval
   edge created by an overlapping chunk starting is not a cut, and drawing one
   there made the figure claim the text was severed when it was not. */
.docv .split{color:var(--l3);font-weight:700;padding:0 2px;
  border-left:2px solid var(--l3);margin-left:2px}
"""

# A conversation as the model sees it: an array of messages that only grows.
MSGS = """
/* message transcript */
.msgs{display:grid;gap:5px;font-family:"IBM Plex Mono",monospace;font-size:0.72rem}
.msg{border:1px solid var(--line);border-left-width:3px;padding:7px 10px;background:var(--surface);
  color:var(--ink-soft);line-height:1.5}
.msg .r{display:block;font-size:0.62rem;letter-spacing:0.1em;text-transform:uppercase;
  color:var(--ink-faint);margin-bottom:4px}
.msg.sys{border-left-color:var(--ink-faint)}
.msg.user{border-left-color:var(--accent)}
.msg.model{border-left-color:var(--l2)}
.msg.tool{border-left-color:var(--l1)}
.msg.err{border-left-color:var(--l3)}
.msg.now{background:var(--surface-2);color:var(--ink)}
.msg b{color:var(--ink);font-weight:600}
.msg .dim{color:var(--ink-faint)}
"""

# Two by two, with the four counts a threshold decides.
CM = """
/* confusion matrix */
.cm{border-collapse:collapse;font-family:"IBM Plex Mono",monospace;font-size:0.72rem;
  width:auto;min-width:0}
.cm th{font-weight:400;color:var(--ink-faint);padding:4px 8px;background:transparent;
  font-size:0.63rem;letter-spacing:0.07em;text-transform:uppercase;white-space:nowrap}
.cm td{border:1px solid var(--line);padding:9px 13px;text-align:center;min-width:66px;
  font-variant-numeric:tabular-nums;color:var(--ink);font-size:0.95rem;font-weight:600}
.cm td small{display:block;font-size:0.6rem;font-weight:400;letter-spacing:0.07em;
  text-transform:uppercase;color:var(--ink-faint);margin-top:3px}
.cm td.tp{background:color-mix(in srgb,var(--l1) 20%,var(--surface))}
.cm td.tn{background:color-mix(in srgb,var(--l1) 9%,var(--surface))}
.cm td.fp{background:color-mix(in srgb,var(--l3) 17%,var(--surface))}
.cm td.fn{background:color-mix(in srgb,var(--l3) 24%,var(--surface))}
"""

# A GPU's time, one column per step, one row per sequence slot.
TL = """
/* scheduling timeline */
.tl{display:grid;gap:2px}
.tl .lane{display:flex;gap:2px;align-items:center}
.tl .lane .lab{min-width:70px;flex:0 0 auto;text-align:right;
  font-family:"IBM Plex Mono",monospace;font-size:0.64rem;color:var(--ink-faint)}
.tl .lane u{display:block;width:15px;height:15px;background:var(--surface-2);
  border:1px solid var(--line);text-decoration:none}
.tl .lane u.pre{background:var(--l3)}
.tl .lane u.dec{background:var(--l2)}
.tl .lane u.idle{background:var(--surface-2)}
/* finished, but the slot is still reserved: the waste a static batch pays */
.tl .lane u.held,.stack-key i.held{background:repeating-linear-gradient(45deg,
  var(--line),var(--line) 3px,var(--surface-2) 3px,var(--surface-2) 6px)}
.tl .lane u.now{outline:2px solid var(--accent);outline-offset:1px}
"""


# Most figures here are steered by three or four numbers rather than played
# through, so the knobs get a panel at the top of the stage instead of being
# crammed into the control bar beside the transport.
KNOBS = """
/* knob panel */
.knobs{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:10px 18px;
  margin:0 0 15px}
.knobs label{display:grid;gap:3px;font-family:"IBM Plex Mono",monospace;font-size:0.65rem;
  letter-spacing:0.05em;color:var(--ink-faint);text-transform:uppercase}
.knobs label .v{color:var(--ink);font-weight:600;text-transform:none;letter-spacing:0;
  font-variant-numeric:tabular-nums}
.knobs input[type=range]{width:100%;accent-color:var(--accent);margin:0}
.knobs select{font-family:"IBM Plex Mono",monospace;font-size:0.7rem;background:var(--surface);
  color:var(--ink);border:1px solid var(--line);padding:4px 6px;width:100%}
.knobs .sw{display:flex}
.knobs .sw button{flex:1 1 0;font-family:"IBM Plex Mono",monospace;font-size:0.64rem;
  background:var(--surface);color:var(--ink-soft);border:1px solid var(--line);
  border-right-width:0;padding:5px 3px;cursor:pointer;white-space:nowrap}
.knobs .sw button:last-child{border-right-width:1px}
.knobs .sw button:hover{color:var(--ink)}
.knobs .sw button[aria-pressed="true"]{background:var(--accent);color:var(--ground);font-weight:600}
.demo-ctl input[type=text].wide{width:30ch}
.trio{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.trio > div{min-width:0}
.trio h6{font-family:"IBM Plex Mono",monospace;font-size:0.63rem;letter-spacing:0.09em;
  text-transform:uppercase;color:var(--ink-faint);margin:0 0 7px;font-weight:600}
@media (max-width:640px){.trio{grid-template-columns:1fr}}
/* two overlapping score distributions, and the threshold drawn through them */
.hist{display:flex;align-items:flex-end;gap:1px;height:118px;position:relative}
.hist .h{flex:1 1 0;height:100%;position:relative}
.hist .h i{position:absolute;left:0;right:0;display:block;font-style:normal}
.hist .h i.neg{background:color-mix(in srgb,var(--ink-faint) 45%,var(--surface));bottom:0}
.hist .h i.pos{background:var(--l2)}
.hist .cut{position:absolute;top:-6px;bottom:-6px;width:2px;background:var(--l3);
  margin-left:-1px;pointer-events:none}
"""

CSS = demo_ui.sheet('ai', ['py', 'ts', 'go'],
                    KNOBS, TOKS, MAT, DIST, demo_ui.CELLS, STACK, DOCV, MSGS, CM, TL,
                    demo_ui.SVG, demo_ui.SPLIT)

EARLY_JS = demo_ui.early_js('ai', 'ai-lang', ['py', 'ts', 'go'], 'py')

BAR = demo_ui.bar([('py', 'Python'), ('ts', 'TypeScript'), ('go', 'Go')], 'py')

JS = demo_ui.switch_js('ai', 'ai-lang', ['py', 'ts', 'go'],
                       [('p', 'py'), ('t', 'ts'), ('g', 'go')])
