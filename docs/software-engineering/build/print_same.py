"""Printing from a dark-themed browser must produce the same ink as a light one.

Compares the colour-and-character profile of two render directories. Anything
that differs is a token whose dark value reached the page."""
import sys, glob, collections
import pymupdf

def profile(d):
    t = collections.Counter()
    for path in sorted(glob.glob(d + '/*.pdf')):
        doc = pymupdf.open(path)
        for page in doc:
            for b in page.get_text("dict")["blocks"]:
                for l in b.get("lines", []):
                    for s in l["spans"]:
                        if s["text"].strip():
                            t[s["color"]] += len(s["text"].strip())
        doc.close()
    return t

a_dir = sys.argv[1] if len(sys.argv) > 1 else "pdf"
b_dir = sys.argv[2] if len(sys.argv) > 2 else "pdf-dark"
a, b = profile(a_dir), profile(b_dir)
print(f"{a_dir}: {len(a)} colours, {sum(a.values())} chars")
print(f"{b_dir}: {len(b)} colours, {sum(b.values())} chars")
diff = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
for k in sorted(diff, key=lambda k: -max(a.get(k, 0), b.get(k, 0))):
    print(f"  differs  #{k:06X}  {a.get(k, 0)} vs {b.get(k, 0)}")
print("\n" + ("IDENTICAL" if not diff else f"{len(diff)} COLOUR(S) DIFFER"))
sys.exit(1 if diff else 0)
