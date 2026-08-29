# -*- coding: utf-8 -*-
"""Assemble aws-deep-dive.html from its fragments, then splice in the chrome the
shared template does not know about: the Go/Python switch and the series rail.
Idempotent -- every insert is anchored and asserted, so rebuilding is a no-op.
"""
import tpl, re, aws_ui
import series

PAGE, TITLE = 'aws-deep-dive.html', 'AWS, Service by Service'
# the bar shows the full name where there is room and just the subject where
# there is not, so the language switch keeps its place on a phone
MARK = ('<span class="m-full">AWS, Service by Service</span>'
        '<span class="m-short">AWS</span>')
FRAGMENTS = ['aws_a.html', 'aws_b.html', 'aws_c.html', 'aws_d.html',
             'aws_e.html', 'aws_f.html', 'aws_g.html', 'aws_h.html']

# The rail lives in series.py so the eight pages cannot drift apart;
# series_sync.py writes the same block into the pages with no build script.
SERIES = series.block('aws-deep-dive.html')

WORDS = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']


def read(f):
    return open(f, encoding='utf-8').read().strip()


hero = read('aws_hero.html')
parts = "\n\n".join(read(f) for f in FRAGMENTS)
foot = read('aws_foot.html')
n = tpl.build(PAGE, TITLE, MARK, hero, parts + "\n" + foot)

s = open(PAGE, encoding='utf-8').read()

# per-topic kickers, numbered in document order
kick = list(re.finditer(r'<span class="kicker">AWS &middot; (\w+)</span>', s))
for i, m in enumerate(reversed(kick)):
    idx = len(kick) - 1 - i
    s = s[:m.start()] + '<span class="kicker">AWS &middot; %02d</span>' % (idx + 1) + s[m.end():]

pw = list(re.finditer(r'<span class="kicker">Part (\w+)</span>', s))
for i, m in enumerate(reversed(pw)):
    idx = len(pw) - 1 - i
    s = s[:m.start()] + '<span class="kicker">Part %s</span>' % WORDS[idx] + s[m.end():]

# language switch: styles and the pre-paint class before the topbar, the control
# inside it, the behaviour after the shared script
assert s.count('<div class="topbar">') == 1
s = s.replace('<div class="topbar">',
              aws_ui.CSS.strip() + '\n' + aws_ui.EARLY_JS.strip() + '\n\n<div class="topbar">', 1)
assert s.count('<button class="toc-toggle"') == 1
s = s.replace('    <button class="toc-toggle"', aws_ui.BAR + '    <button class="toc-toggle"', 1)

anchor = '<p class="toc-foot"'
assert s.count(anchor) == 1, 'expected exactly one toc-foot element'
s = s.replace(anchor, SERIES + '  ' + anchor, 1)
assert '.toc-series{' in s, 'series CSS block missing from the page'

s = s.rstrip() + '\n' + aws_ui.JS.strip() + '\n'

# every topic must carry code in BOTH languages
bad = []
for m in re.finditer(r'<section class="topic" id="([^"]+)">', s):
    end = s.index('</section>', m.end())
    body = s[m.end():end]
    if 'data-lang="go"' not in body or 'data-lang="py"' not in body:
        bad.append(m.group(1))
assert not bad, 'topics missing a language pair: %s' % ' '.join(bad)

open(PAGE, 'w', encoding='utf-8').write(s)
print('topics=%d parts=%d kickers=%d bytes=%d' % (n, len(pw), len(kick), len(s)))
