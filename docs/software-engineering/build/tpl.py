import re, html, sys

HUB = 'backend-go-ladder.html'
_hub = open(HUB, encoding='utf-8').read()

# reuse the hub's exact design system + chrome so the series is visually identical
_styles = re.findall(r'<style>.*?</style>', _hub, re.S)
def _pick(*needles):
    for b in _styles:
        if all(n in b for n in needles): return b
    raise SystemExit('tpl: no style block containing %r' % (needles,))
BASE_STYLE  = _pick('.lvl{')                 # tokens, type, level cards, figures
NAV_STYLE   = _pick('.topbar .progress')     # progress bar + contents rail + drawer
SERIES_STYLE= _pick('.toc-series{')          # cross-page series block
TOPBAR = re.search(r'<div class="topbar">.*?</div>\n</div>', _hub, re.S).group(0)
SCRIPT = re.search(r'<script>.*?</script>', _hub, re.S).group(0)
FONTS = re.search(r'<link rel="preconnect".*?display=swap">', _hub, re.S).group(0)

EXTRA = """
<style>
/* ---------- deep-dive additions ---------- */
.crumb{font-family:"IBM Plex Mono",monospace;font-size:0.7rem;letter-spacing:0.1em;
  text-transform:uppercase;color:var(--ink-faint)}
.crumb a{color:var(--ink-soft);text-decoration:none;border-bottom:1px solid var(--line)}
.crumb a:hover{color:var(--accent);border-bottom-color:var(--accent)}
.numbers{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:0;
  border:1px solid var(--line);background:var(--surface);margin:24px 0}
.numbers div{padding:14px 16px;border-right:1px solid var(--line)}
.numbers div:last-child{border-right:none}
.numbers .v{font-family:"Bricolage Grotesque",sans-serif;font-size:1.5rem;font-weight:700;
  color:var(--accent);font-variant-numeric:tabular-nums;line-height:1.1}
.numbers .k{font-family:"IBM Plex Mono",monospace;font-size:0.66rem;letter-spacing:0.1em;
  text-transform:uppercase;color:var(--ink-faint);margin-top:6px;display:block}
.numbers .d{font-size:0.85rem;color:var(--ink-soft);margin-top:6px;line-height:1.45}
.pair{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin:24px 0}
.note{border:1px solid var(--line);border-left:3px solid var(--lc,var(--accent));
  background:var(--surface);padding:16px 18px;margin:22px 0}
.note h4{margin-bottom:7px}
.note p{margin:0;color:var(--ink-soft);font-size:0.93rem}
.note.warn{--lc:var(--l3)}
.note.warn h4{color:var(--l3)}
.steps{counter-reset:st;list-style:none;padding:0;margin:24px 0}
.steps li{counter-increment:st;position:relative;padding:0 0 16px 44px;color:var(--ink-soft);font-size:0.94rem}
.steps li::before{content:counter(st,decimal-leading-zero);position:absolute;left:0;top:1px;
  font-family:"IBM Plex Mono",monospace;font-size:0.7rem;font-weight:600;color:var(--accent);
  border:1px solid var(--line);padding:3px 6px}
.steps li b{color:var(--ink)}
@media (max-width:640px){.numbers div{border-right:none;border-bottom:1px solid var(--line)}}
</style>
"""

def _toc(parts_html):
    groups, n = [], 0
    for pm in re.finditer(r'<section class="part" id="([^"]+)">(.*?)\n</section>', parts_html, re.S):
        pid, body = pm.group(1), pm.group(2)
        h2 = re.search(r'<h2>(.*?)</h2>', body, re.S)
        label = re.sub(r'<[^>]+>', '', h2.group(1)).strip() if h2 else pid
        items = []
        for tm in re.finditer(r'<section class="topic" id="([^"]+)">.*?<h3>(.*?)</h3>', body, re.S):
            n += 1
            items.append((tm.group(1), re.sub(r'<[^>]+>', '', tm.group(2)).strip(), n))
        groups.append((pid, label, items))
    out = ['<aside class="toc" id="toc" aria-label="Contents">', '  <h2>Contents</h2>']
    for pid, label, items in groups:
        out.append('  <div class="toc-group">')
        out.append('    <a href="#%s">%s</a>' % (pid, label))
        if items:
            out.append('    <ol>')
            for tid, tlabel, i in items:
                out.append('      <li><a href="#%s"><span class="n">%02d</span><span>%s</span></a></li>'
                           % (tid, i, tlabel))
            out.append('    </ol>')
        out.append('  </div>')
    out.append('  <p class="toc-foot" id="toc-foot">%d sections</p>' % n)
    out.append('</aside>')
    return '\n'.join(out), n

def build(path, title, mark, hero, parts_html):
    toc, n = _toc(parts_html)
    topbar = TOPBAR.replace('The Backend Ladder', mark)
    doc = "\n".join([
        '<title>%s</title>' % title, FONTS, '', BASE_STYLE, NAV_STYLE, SERIES_STYLE, EXTRA, '',
        topbar, '', hero, '', parts_html, '',
        '<div class="toc-backdrop" id="toc-backdrop" hidden></div>', '', toc, '', SCRIPT, ''])
    open(path, 'w', encoding='utf-8').write(doc)
    return n
