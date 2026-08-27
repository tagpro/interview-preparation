"""Insert a <pre> code block into named topics of a built page.

Anchored on the topic's <div class="levels"> where it has one, and otherwise on
its closing </section> — a few summary topics are table-driven and carry no
level cards. Either way the table of contents is untouched.
"""
import re


def _topic_span(html, tid):
    m = re.search(r'<section class="topic" id="%s">' % re.escape(tid), html)
    if not m:
        raise SystemExit('codeblocks: no topic id=%r' % tid)
    end = html.index('</section>', m.end())        # topics are never nested
    return m.end(), end


def apply(html: str, blocks: dict) -> str:
    for tid, pre in blocks.items():
        start, end = _topic_span(html, tid)
        lv = html.find('<div class="levels">', start, end)
        at = lv if lv != -1 else end
        html = html[:at] + pre.strip() + '\n\n      ' + html[at:]
    return html


def check(html: str) -> None:
    """Every topic must now carry at least one code block."""
    parts = re.split(r'(?=<section class="topic" id=")', html)
    missing = [re.search(r'id="([^"]+)"', p).group(1)
               for p in parts[1:] if '<pre' not in p.split('</section>')[0]]
    if missing:
        raise SystemExit('codeblocks: still without code: %s' % ' '.join(missing))
    return len(parts) - 1


def pending(html: str, blocks: dict) -> dict:
    """Drop blocks whose topic already carries code — keeps a rebuild idempotent."""
    out = {}
    for tid, pre in blocks.items():
        start, end = _topic_span(html, tid)
        if '<pre' not in html[start:end]:
            out[tid] = pre
    return out
