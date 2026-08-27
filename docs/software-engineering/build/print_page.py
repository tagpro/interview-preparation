"""Render one page of a PDF to PNG at readable resolution."""
import sys, pymupdf
src, pno, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
zoom = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
doc = pymupdf.open(src)
doc[pno - 1].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False).save(out)
print(out)
