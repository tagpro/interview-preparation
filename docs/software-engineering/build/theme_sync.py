# -*- coding: utf-8 -*-
"""Place the colour-theme switch, and hand site_build.mjs its copy.

The switch is a property of the served site, not of the pages: the same pages
are published as artifacts, where the claude.ai host already provides a theme
control and stamps the same `data-theme` attribute. So the nine series pages
must NOT carry the block -- `site_build.mjs` splices it in as it writes the
site, next to the other site-only transformations it already makes.

That leaves two pages `site_build.mjs` does not produce: the site's front page
and its 404, which are hand-written and belong to the site rather than to the
series. Those are written here.

This also writes `theme_block.html`, which is generated, and which
`site_build.mjs` reads. Rebuilding the site without running this first fails
loudly there rather than quietly shipping a site with no switch.

Idempotent, and self-healing: a series page that somehow acquired the block has
it removed.

    python3 theme_sync.py             # write
    python3 theme_sync.py --check     # report only, exit 1 on drift
"""
import os
import re
import sys

import series
import theme_ui

CHECK = '--check' in sys.argv
DOCS = '/home/user/interview-preparation/docs'
GENERATED = 'theme_block.html'

RE = re.compile(re.escape(theme_ui.OPEN) + r'.*?' + re.escape(theme_ui.CLOSE) + r'\n?', re.S)
ANCHOR = '<body>\n'

changed = 0
want = theme_ui.block()

# 1. the copy site_build.mjs splices into the nine pages it writes
if not os.path.exists(GENERATED) or open(GENERATED, encoding='utf-8').read() != want:
    changed += 1
    print('%-26s %s' % (GENERATED, 'regenerated'))
    if not CHECK:
        open(GENERATED, 'w', encoding='utf-8').write(want)
else:
    print('%-26s unchanged' % GENERATED)

# 2. the two hand-written pages site_build.mjs does not produce
for name in ('index.html', '404.html'):
    path = os.path.join(DOCS, name)
    s = open(path, encoding='utf-8').read()
    had = RE.search(s)
    if had and had.group(0).rstrip('\n') == want.rstrip('\n'):
        print('%-26s unchanged' % name)
        continue
    out = RE.sub('', s)
    if ANCHOR not in out:
        raise SystemExit('%s: no <body> to place the theme switch after' % name)
    out = out.replace(ANCHOR, want + ANCHOR, 1)
    changed += 1
    print('%-26s %s' % (name, 'updated' if had else 'added'))
    if not CHECK:
        open(path, 'w', encoding='utf-8').write(out)

# 3. the series pages must not carry it -- the artifacts are published from them
for path, _t, _s, _u in series.PAGES:
    s = open(path, encoding='utf-8').read()
    if not RE.search(s):
        continue
    changed += 1
    print('%-26s REMOVED (site_build.mjs adds it)' % path)
    if not CHECK:
        open(path, 'w', encoding='utf-8').write(RE.sub('', s))

print('\n%d item(s) %s' % (changed, 'differ' if CHECK else 'written'))
sys.exit(1 if CHECK and changed else 0)
