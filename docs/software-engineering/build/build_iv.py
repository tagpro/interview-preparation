# -*- coding: utf-8 -*-
"""Assemble interview-map.html from its fragments, then splice in the chrome the
shared template does not know about: this page's three syllabus components and
the series rail. Idempotent -- every insert is anchored and asserted.
"""
import tpl, re, iv_ui
import series

PAGE, TITLE = 'interview-map.html', 'Everything They Ask'
# the bar shows the full name where there is room and just the subject where
# there is not, matching the AWS page's behaviour on a narrow screen
MARK = ('<span class="m-full">Everything They Ask</span>'
        '<span class="m-short">Interview</span>')
FRAGMENTS = ['iv_a.html', 'iv_b.html', 'iv_c.html', 'iv_d.html', 'iv_e.html',
             'iv_f.html', 'iv_g.html', 'iv_h.html', 'iv_i.html']

SERIES = series.block(PAGE)

WORDS = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
         'ten', 'eleven', 'twelve', 'thirteen', 'fourteen']


def read(f):
    return open(f, encoding='utf-8').read().strip()


hero = read('iv_hero.html')
parts = "\n\n".join(read(f) for f in FRAGMENTS)
foot = read('iv_foot.html')
n = tpl.build(PAGE, TITLE, MARK, hero, parts + "\n" + foot)

s = open(PAGE, encoding='utf-8').read()

# per-topic kickers, numbered in document order; the fragments write a
# placeholder word so a topic can be moved without renumbering by hand
kick = list(re.finditer(r'<span class="kicker">Topic &middot; (\w+)</span>', s))
for i, m in enumerate(reversed(kick)):
    idx = len(kick) - 1 - i
    s = s[:m.start()] + '<span class="kicker">Topic &middot; %02d</span>' % (idx + 1) + s[m.end():]

pw = list(re.finditer(r'<span class="kicker">Part (\w+)</span>', s))
assert len(pw) <= len(WORDS), 'more parts than number words'
for i, m in enumerate(reversed(pw)):
    idx = len(pw) - 1 - i
    s = s[:m.start()] + '<span class="kicker">Part %s</span>' % WORDS[idx] + s[m.end():]

# the page's own components, in front of the bar so nothing paints unstyled
assert s.count('<div class="topbar">') == 1
s = s.replace('<div class="topbar">', iv_ui.CSS.strip() + '\n\n<div class="topbar">', 1)

anchor = '<p class="toc-foot"'
assert s.count(anchor) == 1, 'expected exactly one toc-foot element'
s = s.replace(anchor, SERIES + '  ' + anchor, 1)
assert '.toc-series{' in s, 'series CSS block missing from the page'

# the atlas at the top must name every part, and every name must resolve
ids = re.findall(r'<section class="part" id="([^"]+)">', s)
linked = re.findall(r'<a class="atlas-l" href="#([^"]+)">', s)
assert linked == ids, 'the atlas and the parts disagree:\n  %s\n  %s' % (ids, linked)

open(PAGE, 'w', encoding='utf-8').write(s)
print('topics=%d parts=%d kickers=%d bytes=%d' % (n, len(pw), len(kick), len(s)))
