import tpl, re
import series

PAGE, TITLE, MARK = 'java-spring.html', 'Java, Then Spring', 'Java, Then Spring'

hero = open('java_hero.html', encoding='utf-8').read()
def read(f): return open(f, encoding='utf-8').read().strip()
parts = "\n\n".join([read('java_a.html'), read('java_b.html'),
                     read('java_c.html'), read('java_d.html'),
                     read('java_svc.html')])

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
words = ['one','two','three','four','five','six','seven','eight','nine','ten',
         'eleven','twelve']
pw = list(re.finditer(r'<span class="kicker">Part (\w+)</span>', s))
assert len(pw) <= len(words), 'more parts than number words: extend the list'
for i, m in enumerate(reversed(pw)):
    s = s[:m.start()] + '<span class="kicker">Part %s</span>' % words[len(pw) - 1 - i] + s[m.end():]

# The rail lives in series.py so the eight pages cannot drift apart;
# series_sync.py writes the same block into the pages with no build script.
SERIES = series.block('java-spring.html')
ANCHOR = '<p class="toc-foot"'
assert s.count(ANCHOR) == 1
s = s.replace(ANCHOR, SERIES + '  ' + ANCHOR)
assert '.toc-series{' in s and '.stage{' in s

open(PAGE, 'w', encoding='utf-8').write(s)
print('topics=%d parts=%d kickers=%d bytes=%d' % (n, len(pw), len(kick), len(s)))
