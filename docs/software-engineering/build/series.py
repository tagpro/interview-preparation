# -*- coding: utf-8 -*-
"""The one list of pages in the series, and the rail that renders it.

Every page carries a cross-link rail, and until this module existed each build
script kept its own copy of it. They drifted: the AWS page listed Python before
the cloud page while the other six listed it after, and adding a page meant
editing seven places and missing one. There is now a single list; `block()`
renders it for whichever page is asking, and `series_sync.py` writes the result
into pages that have no build script of their own.
"""

# file, title, subtitle, artifact uuid -- in reading order
PAGES = [
    ('backend-go-ladder.html', 'The Backend Ladder',
     'Overview &middot; all three pillars', '7b938187-b51e-46cf-8191-2f7bca007bd3'),
    ('pillar-a-foundations.html', 'The Machine Room',
     'Deep dive &middot; foundations', '25b57aa1-de16-48d9-bc41-fbd5857dd97f'),
    ('pillar-b-go.html', 'Reading Go',
     'Deep dive &middot; Go', '513b3fa1-6b65-4c47-84da-25734edb3c3f'),
    ('pillar-c-cloud.html', 'From Account to Pod',
     'Deep dive &middot; cloud', '3e17f5fe-161e-41bd-90a9-baca241492b5'),
    ('python-foundations.html', 'Python, End to End',
     'Foundations &middot; Python', '9a2c6334-1c38-40c7-a916-c2fa95d490c4'),
    ('java-spring.html', 'Java, Then Spring',
     'Tutorial &middot; Java + Spring Boot', '5695328e-c427-4d93-b1d2-b7a3d48f675b'),
    ('aws-deep-dive.html', 'AWS, Service by Service',
     'Deep dive &middot; AWS + SDKs', 'd8c052d4-750f-4967-bb0f-7d6a048681e6'),
    ('dsa.html', 'Data Structures, In Motion',
     'Deep dive &middot; algorithms, interactive', 'de1c07a0-10a5-42a5-ac59-582c4a48cc19'),
    ('ai.html', 'Prompt to Production',
     'Deep dive &middot; AI engineering, interactive', '934e618a-db2e-4b3d-8cd1-0d3a58ac2a5c'),
    ('interview-map.html', 'Everything They Ask',
     'Map &middot; the whole technical interview', 'b9b3c754-363e-4a1f-9163-32dda13ac63c'),
]

ART = 'https://claude.ai/code/artifact/%s'


def block(here):
    """The rail as it appears on `here`, which is one of the file names above."""
    assert here in {p[0] for p in PAGES}, 'not a page in the series: %r' % here
    out = ['<div class="toc-series">', '  <h3>The series</h3>']
    for path, title, sub, uuid in PAGES:
        span = '<span class="t">%s</span><span class="s">%s</span>' % (title, sub)
        if path == here:
            out.append('  <a class="here" aria-current="page">%s</a>' % span)
        else:
            out.append('  <a href="%s" target="_blank" rel="noopener">%s</a>'
                       % (ART % uuid, span))
    out.append('</div>')
    return '\n'.join(out) + '\n'
