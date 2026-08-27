# -*- coding: utf-8 -*-
"""Extra code blocks appended to specific Go topics that already have one pre
block but whose lede promises more than that one block demonstrates (e.g. a
five-pattern catalogue with only one pattern coded, a four-category taxonomy
with only two). Anchored on the exact tail of the existing pre (loaded from
extras_data.py, generated verbatim from the built page), and idempotent --
skipped if the marker text is already present.
"""
import extras_data as _d

EXTRAS = {
    "patterns": (_d.PATTERNS_ANCHOR, "worker pool: N goroutines", _d.PATTERNS_ADDITION),
    "taxonomy": (_d.TAXONOMY_ANCHOR, "the fourth category is not a Code at all", _d.TAXONOMY_ADDITION),
}


def apply(html: str) -> str:
    for tid, (anchor, marker, addition) in EXTRAS.items():
        if marker in html:
            continue   # already applied -- idempotent rebuild
        i = html.index('<section class="topic" id="%s">' % tid)
        end = html.index('</section>', i)
        at = html.index(anchor, i, end)
        at_end = at + len(anchor)
        html = html[:at_end] + addition + html[at_end:]
    return html
