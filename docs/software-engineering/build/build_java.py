import tpl, re

PAGE, TITLE, MARK = 'java-spring.html', 'Java, Then Spring', 'Java, Then Spring'

hero = open('java_hero.html', encoding='utf-8').read()
def read(f): return open(f, encoding='utf-8').read().strip()
parts = "\n\n".join([read('java_a.html'), read('java_b.html'),
                     read('java_c.html'), read('java_d.html')])

foot = """<footer class="footer">
  <div class="shell col">
    <p><strong>How this page fits the series.</strong> The systems ideas here &mdash; timeouts, bounded concurrency, idempotency, the transaction boundary &mdash; are the same ones the foundations page teaches language-agnostically. Java&rsquo;s contribution is a compiler and a container that enforce more of them before the code ever runs.</p>
    <p style="margin:0">Everything targets Java 21 (Temurin) and Spring Boot 3.5.x. Where behaviour is version-specific &mdash; virtual threads, sealed switch exhaustiveness, RestClient &mdash; the text says which release introduced it.</p>
  </div>
</footer>"""

n = tpl.build(PAGE, TITLE, MARK, hero, parts + "\n" + foot)
s = open(PAGE, encoding='utf-8').read()

# renumber topic kickers and part words in document order
kick = list(re.finditer(r'<span class="kicker">Java &middot; (\w+)</span>', s))
for i, m in enumerate(reversed(kick)):
    s = s[:m.start()] + '<span class="kicker">Java &middot; %02d</span>' % (len(kick) - i) + s[m.end():]
words = ['one','two','three','four','five','six','seven','eight','nine','ten']
pw = list(re.finditer(r'<span class="kicker">Part (\w+)</span>', s))
for i, m in enumerate(reversed(pw)):
    s = s[:m.start()] + '<span class="kicker">Part %s</span>' % words[len(pw) - 1 - i] + s[m.end():]

SERIES = """<div class="toc-series">
  <h3>The series</h3>
  <a href="https://claude.ai/code/artifact/7b938187-b51e-46cf-8191-2f7bca007bd3" target="_blank" rel="noopener"><span class="t">The Backend Ladder</span><span class="s">Overview &middot; all three pillars</span></a>
  <a href="https://claude.ai/code/artifact/25b57aa1-de16-48d9-bc41-fbd5857dd97f" target="_blank" rel="noopener"><span class="t">The Machine Room</span><span class="s">Deep dive &middot; foundations</span></a>
  <a href="https://claude.ai/code/artifact/513b3fa1-6b65-4c47-84da-25734edb3c3f" target="_blank" rel="noopener"><span class="t">Reading Go</span><span class="s">Deep dive &middot; Go</span></a>
  <a href="https://claude.ai/code/artifact/3e17f5fe-161e-41bd-90a9-baca241492b5" target="_blank" rel="noopener"><span class="t">From Account to Pod</span><span class="s">Deep dive &middot; cloud</span></a>
  <a href="https://claude.ai/code/artifact/9a2c6334-1c38-40c7-a916-c2fa95d490c4" target="_blank" rel="noopener"><span class="t">Python, End to End</span><span class="s">Foundations &middot; Python</span></a>
  <a class="here" aria-current="page"><span class="t">Java, Then Spring</span><span class="s">Tutorial &middot; Java + Spring Boot</span></a>
  <a href="https://claude.ai/code/artifact/d8c052d4-750f-4967-bb0f-7d6a048681e6" target="_blank" rel="noopener"><span class="t">AWS, Service by Service</span><span class="s">Deep dive &middot; AWS + SDKs</span></a>
</div>
"""
ANCHOR = '<p class="toc-foot"'
assert s.count(ANCHOR) == 1
s = s.replace(ANCHOR, SERIES + '  ' + ANCHOR)
assert '.toc-series{' in s and '.stage{' in s

open(PAGE, 'w', encoding='utf-8').write(s)
print('topics=%d parts=%d kickers=%d bytes=%d' % (n, len(pw), len(kick), len(s)))
