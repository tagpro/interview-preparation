import tpl, re, codeblocks, py_code, go_code
hero=open('py_hero.html',encoding='utf-8').read()
def read(f): return open(f,encoding='utf-8').read().strip()

# py_c holds two parts: perf, then production. The new toolchain and ecosystem
# parts belong between them so the review checklist stays the finale.
c=read('py_c.html')
cut=c.index('<section class="part" id="production">')
c_perf, c_prod = c[:cut].rstrip(), c[cut:]

parts="\n\n".join([read('py_a.html'), read('py_b.html'), c_perf,
                   read('py_d.html'), read('py_e.html'), read('py_cook.html'), c_prod])
foot=open('py_foot.html',encoding='utf-8').read()
n=tpl.build('python-foundations.html','Python, End to End','Python, End to End',hero,parts+"\n"+foot)

s=open('python-foundations.html',encoding='utf-8').read()
# renumber the per-topic kickers in document order
kick=list(re.finditer(r'<span class="kicker">Python &middot; (\w+)</span>', s))
for i,m in enumerate(reversed(kick)):
    idx=len(kick)-1-i
    s = s[:m.start()] + '<span class="kicker">Python &middot; %02d</span>'%(idx+1) + s[m.end():]
# renumber part words
words=['one','two','three','four','five','six','seven','eight','nine','ten']
pw=list(re.finditer(r'<span class="kicker">Part (\w+)</span>', s))
for i,m in enumerate(reversed(pw)):
    idx=len(pw)-1-i
    s = s[:m.start()] + '<span class="kicker">Part %s</span>'%words[idx] + s[m.end():]
SERIES = """<div class="toc-series">
  <h3>The series</h3>
  <a href="https://claude.ai/code/artifact/7b938187-b51e-46cf-8191-2f7bca007bd3" target="_blank" rel="noopener"><span class="t">The Backend Ladder</span><span class="s">Overview &middot; all three pillars</span></a>
  <a href="https://claude.ai/code/artifact/25b57aa1-de16-48d9-bc41-fbd5857dd97f" target="_blank" rel="noopener"><span class="t">The Machine Room</span><span class="s">Deep dive &middot; foundations</span></a>
  <a href="https://claude.ai/code/artifact/513b3fa1-6b65-4c47-84da-25734edb3c3f" target="_blank" rel="noopener"><span class="t">Reading Go</span><span class="s">Deep dive &middot; Go</span></a>
  <a href="https://claude.ai/code/artifact/3e17f5fe-161e-41bd-90a9-baca241492b5" target="_blank" rel="noopener"><span class="t">From Account to Pod</span><span class="s">Deep dive &middot; cloud</span></a>
  <a class="here" aria-current="page"><span class="t">Python, End to End</span><span class="s">Foundations &middot; Python</span></a>
  <a href="https://claude.ai/code/artifact/5695328e-c427-4d93-b1d2-b7a3d48f675b" target="_blank" rel="noopener"><span class="t">Java, Then Spring</span><span class="s">Tutorial &middot; Java + Spring Boot</span></a>
  <a href="https://claude.ai/code/artifact/d8c052d4-750f-4967-bb0f-7d6a048681e6" target="_blank" rel="noopener"><span class="t">AWS, Service by Service</span><span class="s">Deep dive &middot; AWS + SDKs</span></a>
</div>
"""
ANCHOR = '<p class="toc-foot"'
assert s.count(ANCHOR) == 1, 'expected exactly one toc-foot element'
s = s.replace(ANCHOR, SERIES + '  ' + ANCHOR)
assert '.toc-series{' in s, 'series CSS block missing from the page'

s = codeblocks.apply(s, py_code.BLOCKS)
codeblocks.check(s)

open('python-foundations.html','w',encoding='utf-8').write(s)
print('topics=%d parts=%d kickers=%d bytes=%d'%(n,len(pw),len(kick),len(s)))
