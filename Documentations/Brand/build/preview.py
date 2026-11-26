import sys, fitz
from PIL import Image
pdf = sys.argv[1]
pages = [int(x) for x in sys.argv[2].split(',')]
doc = fitz.open(pdf)
ims = []
for p in pages:
    pix = doc[p - 1].get_pixmap(matrix=fitz.Matrix(0.75, 0.75))
    ims.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
cols = 2
rows = (len(ims) + 1) // 2
w, h = ims[0].size
sheet = Image.new("RGB", (w * cols + 10, h * rows + 10 * (rows - 1)), "#888")
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * (w + 10), (i // cols) * (h + 10)))
out = sys.argv[3] if len(sys.argv) > 3 else "_sheet.png"
sheet.save(out)
print(out, len(doc), "pages total")

