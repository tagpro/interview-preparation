"""Every colour that actually reached the paper, checked against white.

The point is the dark theme: a reader printing from a dark-themed browser must
not get pale text on an unprinted white page. This reads the colours out of the
rendered PDF rather than trusting the stylesheet, so a token that leaked its
dark value shows up here whatever the reason."""
import sys, glob, os, collections
import pymupdf

def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def ratio_to_white(rgb):
    r, g, b = (rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255
    lum = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    return 1.05 / (lum + 0.05)

MIN = 3.0        # even the quietest grey must clear this on paper
seen = collections.Counter()
for path in sorted(glob.glob(sys.argv[1] if len(sys.argv) > 1 else "pdf/*.pdf")):
    doc = pymupdf.open(path)
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l["spans"]:
                    if s["text"].strip():
                        seen[s["color"]] += len(s["text"].strip())
    doc.close()

bad = 0
for color, chars in sorted(seen.items(), key=lambda kv: -kv[1]):
    r = ratio_to_white(color)
    ok = r >= MIN
    if not ok:
        bad += 1
    print(f"{'  ok' if ok else 'FAIL'}  #{color:06X}  {r:5.2f}:1  {chars:>7} chars")
print(f"\n{len(seen)} distinct text colours, {'ALL PASS' if not bad else str(bad) + ' TOO LIGHT'}")
sys.exit(1 if bad else 0)
