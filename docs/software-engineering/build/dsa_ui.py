# -*- coding: utf-8 -*-
"""The stages the algorithms page draws into, plus its language switch.

Everything shared with the other interactive page -- the player, the chrome
around a figure, the switch behaviour, the cell and SVG stages -- lives in
demo_ui.py. What is left here is the three stages only this page has: the bar
chart the sorts run in, the grid the pathfinders explore, and the table the
dynamic-programming demos fill.

The switch works the way the AWS page's does -- every language-specific block
carries data-lang="go", "py" or "java", the root element carries lang-go /
lang-py / lang-java, and CSS hides the other two. With JavaScript off all three
are simply visible, which is a working page rather than a blank one. The choice
is stored under the series' own key, so a reader who picked Python here keeps
Python on the AWS page (which knows only Go and Python, and falls back to Go for
a reader who picked Java).
"""

import demo_ui

BARS = '/* bars: the sorting stage */\n.bars{display:flex;align-items:flex-end;gap:2px;height:180px}\n.bars .bar{flex:1 1 0;min-width:3px;background:var(--ink-faint);position:relative}\n.bars .bar.ok{background:var(--l1)}\n.bars .bar.cmp{background:var(--l2)}\n.bars .bar.mv{background:var(--l3)}\n.bars .bar.piv{background:var(--l3);outline:2px solid var(--l3);outline-offset:1px}\n.bars .bar.dim{opacity:0.34}\n\n'

GRID = '/* grid: the pathfinding stage */\n.grid{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);width:max-content}\n.grid b{width:var(--cs,17px);height:var(--cs,17px);background:var(--surface);display:block;\n  cursor:pointer;font-weight:400}\n.grid b.wall{background:var(--ink-soft);cursor:pointer}\n.grid b.seen{background:color-mix(in srgb,var(--l2) 26%,var(--surface))}\n.grid b.frontier{background:var(--l2);}\n.grid b.path{background:var(--l1)}\n.grid b.src{background:var(--l1);box-shadow:inset 0 0 0 2px var(--ground)}\n.grid b.dst{background:var(--l3);box-shadow:inset 0 0 0 2px var(--ground)}\n.grid b.slow{background:var(--surface-2);box-shadow:inset 0 0 0 1px var(--line)}\n.grid b.slow.seen{background:color-mix(in srgb,var(--l2) 26%,var(--surface-2))}\n\n'

DP = '/* dp table */\n.dp{border-collapse:collapse;font-family:"IBM Plex Mono",monospace;font-size:0.72rem;\n  min-width:0;width:auto}\n.dp td,.dp th{border:1px solid var(--line);padding:3px 6px;text-align:center;min-width:28px;\n  color:var(--ink-faint);font-variant-numeric:tabular-nums;background:transparent}\n.dp th{font-size:0.7rem;color:var(--ink);font-weight:600;letter-spacing:0;text-transform:none;\n  font-family:"IBM Plex Mono",monospace;background:transparent}\n.dp td.set{color:var(--ink)}\n.dp td.now{background:var(--l2);color:var(--ground);font-weight:600}\n.dp td.dep{box-shadow:inset 0 0 0 2px var(--l3)}\n.dp td.trace{background:var(--l1);color:var(--ground);font-weight:600}\n\n'

CSS = demo_ui.sheet('lang', ['go', 'py', 'java'],
                    BARS, demo_ui.CELLS, demo_ui.ROWS, GRID, DP, demo_ui.SVG, demo_ui.SPLIT)

EARLY_JS = demo_ui.early_js('lang', 'ladder-lang', ['py', 'go', 'java'], 'go')

BAR = demo_ui.bar([('go', 'Go'), ('py', 'Python'), ('java', 'Java')], 'go')

JS = demo_ui.switch_js('lang', 'ladder-lang', ['go', 'py', 'java'],
                       [('g', 'go'), ('p', 'py'), ('j', 'java')])
