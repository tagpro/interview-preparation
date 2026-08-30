# -*- coding: utf-8 -*-
"""Escape stray markup characters inside <pre> blocks in a page's fragments.

A bare "<" inside a code block is a tag to every regex-based tool downstream:
the highlighter loses the text after it, the glossary pass mis-scans, and the
dimming verifier reports characters that vanished. On the algorithms page this
was found late, in 54 places, and fixed by hand.

So the fragments for this page are written with ordinary "<", "&" and ">" in
the code, and this pass escapes them on the way in. The only markup a <pre> may
carry is the comment span the fragments use to grey out commentary, which is
preserved verbatim.

Idempotent: entities that are already escaped are left alone, so running it
twice changes nothing.

    python3 esc_pre.py ai_*.html          # rewrite
    python3 esc_pre.py --check ai_*.html  # report only, exit 1 if anything to do
"""
import re
import sys

KEEP = re.compile(r'<span class="c">|</span>')
ENTITY = re.compile(r'&(?:[a-zA-Z][a-zA-Z0-9]{1,9}|#\d{1,6}|#[xX][0-9a-fA-F]{1,5});')
PRE = re.compile(r'(<pre\b[^>]*>)(.*?)(</pre>)', re.S)


def escape(text):
    """Escape one run of code text, leaving existing entities intact."""
    out, at = [], 0
    for m in ENTITY.finditer(text):
        out.append(_plain(text[at:m.start()]))
        out.append(m.group(0))
        at = m.end()
    out.append(_plain(text[at:]))
    return ''.join(out)


def _plain(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def fix_body(body):
    out, at = [], 0
    for m in KEEP.finditer(body):
        out.append(escape(body[at:m.start()]))
        out.append(m.group(0))
        at = m.end()
    out.append(escape(body[at:]))
    return ''.join(out)


def main(argv):
    check = '--check' in argv
    files = [a for a in argv if not a.startswith('--')]
    dirty = 0
    for path in files:
        s = open(path, encoding='utf-8').read()
        n = [0]

        def one(m):
            fixed = fix_body(m.group(2))
            if fixed != m.group(2):
                n[0] += 1
            return m.group(1) + fixed + m.group(3)

        out = PRE.sub(one, s)
        if out != s:
            dirty += n[0]
            print('%-16s %d block(s) escaped' % (path, n[0]))
            if not check:
                open(path, 'w', encoding='utf-8').write(out)
        else:
            print('%-16s clean' % path)
    print('\n%d block(s) %s' % (dirty, 'need escaping' if check else 'rewritten'))
    return 1 if check and dirty else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
