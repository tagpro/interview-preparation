"""Contact sheet of a rendered PDF: every page as a thumbnail on one image, so a
whole printed document can be scanned at a glance for bad breaks and gaps."""
import sys, math, pymupdf

src, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 8
first = int(sys.argv[4]) if len(sys.argv) > 4 else 1
last = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 6

doc = pymupdf.open(src)
pages = [p for p in range(doc.page_count) if first <= p + 1 <= last]
rows = math.ceil(len(pages) / cols)
zoom = 0.32
w = int(doc[0].rect.width * zoom); h = int(doc[0].rect.height * zoom)
pad = 6
sheet = pymupdf.open()
page = sheet.new_page(width=cols * (w + pad) + pad, height=rows * (h + pad + 10) + pad)
page.draw_rect(page.rect, color=(0.75, 0.75, 0.78), fill=(0.75, 0.75, 0.78))
for i, pno in enumerate(pages):
    r, c = divmod(i, cols)
    x = pad + c * (w + pad); y = pad + r * (h + pad + 10)
    pix = doc[pno].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    rect = pymupdf.Rect(x, y, x + w, y + h)
    page.insert_image(rect, pixmap=pix)
    page.draw_rect(rect, color=(0.45, 0.45, 0.5), width=0.5)
    page.insert_text((x + 2, y + h + 8), str(pno + 1), fontsize=7, color=(0.15, 0.15, 0.2))
page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False).save(out)
print(out, f"{len(pages)} pages")
