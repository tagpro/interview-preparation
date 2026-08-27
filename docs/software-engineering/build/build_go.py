"""Rebuild pillar-b-go.html from itself, splicing in the cookbook part and the
per-topic code blocks.

The page was originally assembled from fragments that no longer map cleanly to
its part order, so the built page is the source of truth: explode it back into
(hero, parts), insert, and re-run tpl.build. Both inserts are idempotent, so
rebuilding twice is a no-op.
"""
import tpl, re, codeblocks, go_code, go_extra

PAGE, TITLE, MARK = 'pillar-b-go.html', 'Reading Go', 'Reading Go'
src = open(PAGE, encoding='utf-8').read()


def build():
    series = re.search(r'<div class="toc-series">.*?\n</div>', src, re.S).group(0)

    # hero: between the topbar and the first part; parts: up to the contents rail
    i_hero = src.index('</div>\n</div>\n', src.index('<div class="topbar">')) + len('</div>\n</div>\n')
    i_part = src.index('<section class="part" id=')
    i_end = src.index('<div class="toc-backdrop"')
    hero, parts = src[i_hero:i_part].strip(), src[i_part:i_end].strip()

    # the cookbook goes before the closing craft part, so the checklist stays last
    anchor = '<section class="part" id="craft">'
    assert parts.count(anchor) == 1
    if 'id="cookbook"' not in parts:
        cook = open('go_cook.html', encoding='utf-8').read().strip()
        parts = parts.replace(anchor, cook + '\n\n' + anchor)

    n = tpl.build(PAGE, TITLE, MARK, hero, parts)
    s = open(PAGE, encoding='utf-8').read()

    kick = list(re.finditer(r'<span class="kicker">Go deep &middot; (\w+)</span>', s))
    for i, m in enumerate(reversed(kick)):
        s = s[:m.start()] + '<span class="kicker">Go deep &middot; %02d</span>' % (len(kick) - i) + s[m.end():]

    words = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
    pw = list(re.finditer(r'<span class="kicker">Part (\w+)</span>', s))
    for i, m in enumerate(reversed(pw)):
        s = s[:m.start()] + '<span class="kicker">Part %s</span>' % words[len(pw) - 1 - i] + s[m.end():]

    tocfoot = '<p class="toc-foot"'
    assert s.count(tocfoot) == 1
    s = s.replace(tocfoot, series + '\n  ' + tocfoot)
    assert '.toc-series{' in s, 'series CSS missing'

    s = codeblocks.apply(s, codeblocks.pending(s, go_code.BLOCKS))
    codeblocks.check(s)
    s = go_extra.apply(s)

    open(PAGE, 'w', encoding='utf-8').write(s)
    print('topics=%d parts=%d kickers=%d bytes=%d' % (n, len(pw), len(kick), len(s)))


try:
    build()
except BaseException:
    open(PAGE, 'w', encoding='utf-8').write(src)   # tpl.build overwrites it early
    raise
