# -*- coding: utf-8 -*-
"""Rewrite the cross-link rail in every built page from series.py.

Three of the eight pages are hand-maintained and have no build script, so the
rail cannot live only in the build scripts. This pass writes it into all eight,
which also means adding a page is one edit to series.py and one run of this.

Idempotent: a page whose rail already matches is left byte-identical.

    python3 series_sync.py            # write
    python3 series_sync.py --check    # report only
"""
import re
import sys

import series

CHECK = '--check' in sys.argv
RE = re.compile(r'<div class="toc-series">.*?</div>\n', re.S)

changed = 0
for path, title, _sub, _uuid in series.PAGES:
    s = open(path, encoding='utf-8').read()
    m = RE.search(s)
    if not m:
        raise SystemExit('%s: no toc-series block' % path)
    want = series.block(path)
    if m.group(0) == want:
        print('%-26s unchanged' % path)
        continue
    changed += 1
    print('%-26s REWRITTEN' % path)
    if not CHECK:
        open(path, 'w', encoding='utf-8').write(s[:m.start()] + want + s[m.end():])

print('\n%d page(s) %s' % (changed, 'differ' if CHECK else 'rewritten'))
sys.exit(1 if CHECK and changed else 0)
