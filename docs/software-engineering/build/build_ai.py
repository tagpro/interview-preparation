# -*- coding: utf-8 -*-
"""Assemble ai.html from its fragments, then splice in the chrome the shared
template does not know about: the Python/TypeScript/Go switch, the interactive
figures, and the series rail.

Idempotent -- every insert is anchored and asserted, so rebuilding is a no-op.
"""
import re
import series

import ai_demos
import ai_ui
import tpl

PAGE, TITLE = 'ai.html', 'Prompt to Production'
# the bar shows the full name where there is room and just the subject where
# there is not, so the language switch keeps its place on a phone
MARK = ('<span class="m-full">AI Engineering</span>'
        '<span class="m-short">AI</span>')
FRAGMENTS = ['ai_a.html', 'ai_b.html', 'ai_c.html', 'ai_d.html',
             'ai_e.html', 'ai_f.html', 'ai_g.html', 'ai_h.html']

# The rail lives in series.py so the pages cannot drift apart;
# series_sync.py writes the same block into the pages with no build script.
SERIES = series.block('ai.html')

WORDS = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
         'nine', 'ten']


def read(f):
    return open(f, encoding='utf-8').read().strip()


hero = read('ai_hero.html')
parts = "\n\n".join(read(f) for f in FRAGMENTS)
foot = read('ai_foot.html')
n = tpl.build(PAGE, TITLE, MARK, hero, parts + "\n" + foot)

s = open(PAGE, encoding='utf-8').read()

# per-topic kickers, numbered in document order
kick = list(re.finditer(r'<span class="kicker">AI &middot; (\w+)</span>', s))
for i, m in enumerate(reversed(kick)):
    idx = len(kick) - 1 - i
    s = s[:m.start()] + '<span class="kicker">AI &middot; %02d</span>' % (idx + 1) + s[m.end():]

pw = list(re.finditer(r'<span class="kicker">Part (\w+)</span>', s))
for i, m in enumerate(reversed(pw)):
    idx = len(pw) - 1 - i
    s = s[:m.start()] + '<span class="kicker">Part %s</span>' % WORDS[idx] + s[m.end():]

# language switch and demo chrome: styles and the pre-paint class before the
# topbar, the control inside it, the behaviour after the shared script
assert s.count('<div class="topbar">') == 1
s = s.replace('<div class="topbar">',
              ai_ui.CSS.strip() + '\n' + ai_ui.EARLY_JS.strip() + '\n\n<div class="topbar">', 1)
assert s.count('<button class="toc-toggle"') == 1
s = s.replace('    <button class="toc-toggle"', ai_ui.BAR + '    <button class="toc-toggle"', 1)

anchor = '<p class="toc-foot"'
assert s.count(anchor) == 1, 'expected exactly one toc-foot element'
s = s.replace(anchor, SERIES + '  ' + anchor, 1)
assert '.toc-series{' in s, 'series CSS block missing from the page'

s = s.rstrip() + '\n' + ai_ui.JS.strip() + '\n' + ai_demos.JS.strip() + '\n'

# every topic must carry code in ALL THREE languages
bad = []
for m in re.finditer(r'<section class="topic" id="([^"]+)">', s):
    end = s.index('</section>', m.end())
    body = s[m.end():end]
    missing = [k for k in ('py', 'ts', 'go') if 'data-lang="%s"' % k not in body]
    if missing:
        bad.append('%s(%s)' % (m.group(1), ','.join(missing)))
assert not bad, 'topics missing a language: %s' % ' '.join(bad)

# every interactive figure must name a demo the script actually registers
demos = set(re.findall(r'data-demo="([^"]+)"', s))
registered = set(re.findall(r'\breg\("([^"]+)"', ai_demos.JS))
assert demos <= registered, 'no such demo: %s' % ' '.join(sorted(demos - registered))
assert registered <= demos, 'demo registered but never used: %s' % ' '.join(sorted(registered - demos))

# a <pre> body may only carry the comment span; a bare "<" downstream is a tag
stray = []
for m in re.finditer(r'<pre[^>]*>(.*?)</pre>', s, re.S):
    body = re.sub(r'<span class="[a-z-]+">|</span>', '', m.group(1))
    if '<' in body or '>' in body:
        stray.append(body[max(0, body.index('<') - 30):][:60] if '<' in body else body[:60])
assert not stray, 'unescaped markup in a code block: %r' % stray[:3]

open(PAGE, 'w', encoding='utf-8').write(s)
print('topics=%d parts=%d kickers=%d demos=%d bytes=%d'
      % (n, len(pw), len(kick), len(demos), len(s)))
