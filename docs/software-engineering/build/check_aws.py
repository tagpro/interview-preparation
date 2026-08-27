# -*- coding: utf-8 -*-
"""Fragment self-check: SVG well-formedness, escaping, and language pairing."""
import xml.dom.minidom, re, sys

ENTS = {'&mdash;': '-', '&ndash;': '-', '&rarr;': '~', '&larr;': '~', '&middot;': '.',
        '&hellip;': '.', '&rsquo;': "'", '&lsquo;': "'", '&ldquo;': '"', '&rdquo;': '"',
        '&times;': 'x', '&nbsp;': ' ', '&ge;': '~', '&le;': '~', '&rArr;': '~',
        '&micro;': 'u', '&asymp;': '~', '&ne;': '~', '&infin;': '8', '&deg;': 'o',
        '&frac12;': 'h', '&sup2;': '2', '&bull;': '.', '&dagger;': '+', '&darr;': '~',
        '&uarr;': '~', '&harr;': '~', '&para;': 'P', '&sect;': 'S', '&copy;': 'c'}

bad = 0
for path in sys.argv[1:]:
    s = open(path, encoding='utf-8').read()

    for i, m in enumerate(re.finditer(r'<svg.*?</svg>', s, re.S)):
        t = m.group(0)
        for k, v in ENTS.items():
            t = t.replace(k, v)
        try:
            xml.dom.minidom.parseString(t)
        except Exception as e:
            print(path, 'SVG', i, 'FAIL', e)
            bad += 1

    # only a colour if it sits in a paint attribute -- "ORDER#9001" is a sort key
    hexes = re.findall(r'(?:fill|stroke|color|stop-color|style)="[^"]*(#[0-9a-fA-F]{3,8})', s)
    if hexes:
        print(path, 'literal hex colour', hexes[:5])
        bad += 1
    if s.count('<pre') != s.count('</pre>'):
        print(path, 'unbalanced pre')
        bad += 1

    for i, m in enumerate(re.finditer(r'<pre[^>]*>(.*?)</pre>', s, re.S)):
        body = re.sub(r'</?span[^>]*>', '', m.group(1))
        st = body
        for k in ('&lt;', '&gt;', '&amp;', '&rarr;', '&mdash;', '&hellip;', '&larr;',
                  '&middot;', '&rsquo;', '&times;', '&ndash;'):
            st = st.replace(k, '')
        if '<' in st or '>' in st:
            print(path, 'raw angle bracket in pre', i, repr(st[max(0, st.find('<') - 60):][:120]))
            bad += 1
        if '&' in st:
            print(path, 'bare ampersand in pre', i, repr(st[max(0, st.find('&') - 60):][:120]))
            bad += 1

    # every topic wants a figure and both languages
    for m in re.finditer(r'<section class="topic" id="([^"]+)">', s):
        end = s.index('</section>', m.end())
        body = s[m.end():end]
        for need, why in (('<svg', 'no figure'), ('data-lang="go"', 'no Go block'),
                          ('data-lang="py"', 'no Python block')):
            if need not in body:
                print(path, 'topic', m.group(1), why)
                bad += 1

    dangling = re.findall(r'&(?![a-zA-Z]{2,8};|#\d{2,5};)', re.sub(r'<pre[^>]*>.*?</pre>', '', s, flags=re.S))
    if dangling:
        print(path, 'bare ampersand outside pre x%d' % len(dangling))
        bad += 1

    print('%-16s svgs=%-3d topics=%-3d pre=%-3d tables=%-2d bytes=%d' % (
        path, len(re.findall(r'<svg', s)), len(re.findall(r'class="topic"', s)),
        len(re.findall(r'<pre', s)), len(re.findall(r'<table', s)), len(s)))

print('BAD:', bad)
sys.exit(1 if bad else 0)
