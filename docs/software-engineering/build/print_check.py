"""Check the rendered PDFs for the two failures a print stylesheet actually has:
text that ran off the page (a scroll bar became a clip) and pages that came out
blank or nearly blank (a forced break landed badly)."""
import sys, glob, os
import pymupdf

MARGIN_PT = 13 / 25.4 * 72          # the @page side margin
TOL = 2                              # points of slack for antialiased glyph boxes

def check(path):
    doc = pymupdf.open(path)
    over, blank, thin = [], [], []
    for i, page in enumerate(doc):
        right = page.rect.width - MARGIN_PT + TOL
        left = MARGIN_PT - TOL
        worst = 0
        d = page.get_text("dict")
        ink = 0
        for b in d["blocks"]:
            for l in b.get("lines", []):
                for s in l["spans"]:
                    if not s["text"].strip():
                        continue
                    ink += len(s["text"].strip())
                    if s["bbox"][2] > right:
                        worst = max(worst, s["bbox"][2] - right)
                    if s["bbox"][0] < left:
                        worst = max(worst, left - s["bbox"][0])
        drawings = len(page.get_drawings())
        if worst:
            over.append((i + 1, round(worst, 1)))
        if ink == 0 and drawings < 3:
            blank.append(i + 1)
        elif ink < 60 and drawings < 3:
            thin.append((i + 1, ink))
    name = os.path.basename(path)
    print(f"{name:<30} {doc.page_count:>3} pages", end="")
    print(f"   overflow: {'none' if not over else over[:6]}", end="")
    print(f"   blank: {'none' if not blank else blank}", end="")
    print(f"   sparse: {'none' if not thin else thin[:6]}")
    doc.close()
    return len(over), len(blank)

bad = 0
for p in sorted(glob.glob(sys.argv[1] if len(sys.argv) > 1 else "pdf/*.pdf")):
    o, b = check(p)
    bad += o + b
print(("\nCLEAN" if bad == 0 else f"\n{bad} pages need attention"))
