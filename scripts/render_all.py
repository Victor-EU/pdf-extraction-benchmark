#!/usr/bin/env python3
"""Render every page of all PDFs to PNG, capped at MAXDIM px on the long side.

Cap keeps images <2000px (Claude multi-image limit) and token-reasonable, while
staying sharp enough for Landing AI table parsing. Writes ground_truth/render_full/
and a _manifest.json listing every page.
"""
import sys, os, glob, json
import fitz

MAXDIM = 1600


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "Data"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "ground_truth/render_full"
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 150
    maxdim = int(sys.argv[4]) if len(sys.argv) > 4 else MAXDIM
    os.makedirs(out_dir, exist_ok=True)
    manifest = []
    for pdf in sorted(glob.glob(os.path.join(data_dir, "*.pdf"))):
        name = os.path.splitext(os.path.basename(pdf))[0]
        doc = fitz.open(pdf)
        npages = doc.page_count
        for i in range(npages):
            page = doc[i]
            zoom = dpi / 72
            # cap long side
            w = page.rect.width * zoom
            h = page.rect.height * zoom
            longside = max(w, h)
            if longside > maxdim:
                zoom *= maxdim / longside
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            fn = f"{name}__p{i+1:04d}.png"
            pix.save(os.path.join(out_dir, fn))
            manifest.append(dict(doc=name, page=i + 1, png=fn))
        doc.close()
        print(f"{name}: {npages} pages")
    json.dump(manifest, open(os.path.join(out_dir, "_manifest.json"), "w"), indent=2)
    print(f"Total rendered: {len(manifest)} -> {out_dir}")


if __name__ == "__main__":
    main()
