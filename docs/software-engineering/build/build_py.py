import tpl, re, codeblocks, py_code, go_code
import series
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
# The rail lives in series.py so the eight pages cannot drift apart;
# series_sync.py writes the same block into the pages with no build script.
SERIES = series.block('python-foundations.html')
ANCHOR = '<p class="toc-foot"'
assert s.count(ANCHOR) == 1, 'expected exactly one toc-foot element'
s = s.replace(ANCHOR, SERIES + '  ' + ANCHOR)
assert '.toc-series{' in s, 'series CSS block missing from the page'

s = codeblocks.apply(s, py_code.BLOCKS)
codeblocks.check(s)

open('python-foundations.html','w',encoding='utf-8').write(s)
print('topics=%d parts=%d kickers=%d bytes=%d'%(n,len(pw),len(kick),len(s)))
