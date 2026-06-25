import sys, fitz
pdf, outprefix = sys.argv[1], sys.argv[2]
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 80
doc = fitz.open(pdf)
print("pages:", len(doc))
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=dpi)
    pix.save(f"{outprefix}-p{i+1}.png")
