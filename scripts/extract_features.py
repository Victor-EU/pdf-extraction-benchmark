#!/usr/bin/env python3
"""Deterministic per-page feature extraction + heuristic 6-category label.

One of three independent ground-truth signals. PyMuPDF only, fully deterministic.

6 categories: Text, Table, Chart/Diagram, Mixed, Cover/Divider, Image/Photo
"""
import sys, json, glob, os
import fitz  # PyMuPDF

CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]


def rects_area_frac(rects, page_area):
    """Approx fraction of page covered by a list of rects (union via grid sampling)."""
    if not rects or page_area <= 0:
        return 0.0
    # crude union: sum areas, clamp. Overlap double-counts but this is a signal only.
    total = 0.0
    for r in rects:
        try:
            a = abs(r.width * r.height)
        except Exception:
            a = 0.0
        total += a
    return min(total / page_area, 1.0)


def page_features(page):
    pr = page.rect
    page_area = pr.width * pr.height
    text = page.get_text("text") or ""
    char_count = len(text.strip())
    words = page.get_text("words") or []
    word_count = len(words)

    # text coverage: union bbox area of text blocks
    text_rects = []
    try:
        for b in page.get_text("blocks"):
            # block = (x0,y0,x1,y1, text, block_no, block_type) ; type 0 = text
            if len(b) >= 7 and b[6] == 0 and b[4].strip():
                text_rects.append(fitz.Rect(b[0], b[1], b[2], b[3]))
    except Exception:
        pass
    text_area_frac = rects_area_frac(text_rects, page_area)

    # images
    img_rects = []
    try:
        for img in page.get_images(full=True):
            xref = img[0]
            for r in page.get_image_rects(xref):
                img_rects.append(r)
    except Exception:
        pass
    n_images = len(img_rects)
    image_area_frac = rects_area_frac(img_rects, page_area)

    # vector drawings (charts/diagrams are vector-heavy)
    n_drawings = 0
    draw_rects = []
    try:
        drawings = page.get_drawings()
        n_drawings = len(drawings)
        for d in drawings:
            r = d.get("rect")
            if r is not None:
                draw_rects.append(r)
    except Exception:
        pass
    drawing_area_frac = rects_area_frac(draw_rects, page_area)

    # tables
    n_tables = 0
    table_area_frac = 0.0
    try:
        tf = page.find_tables()
        tbls = list(tf.tables)
        n_tables = len(tbls)
        t_rects = [fitz.Rect(t.bbox) for t in tbls if t.bbox]
        table_area_frac = rects_area_frac(t_rects, page_area)
    except Exception:
        pass

    content_frac = min(text_area_frac + image_area_frac + drawing_area_frac, 1.0)

    return dict(
        char_count=char_count,
        word_count=word_count,
        n_images=n_images,
        image_area_frac=round(image_area_frac, 3),
        n_drawings=n_drawings,
        drawing_area_frac=round(drawing_area_frac, 3),
        n_tables=n_tables,
        table_area_frac=round(table_area_frac, 3),
        text_area_frac=round(text_area_frac, 3),
        content_frac=round(content_frac, 3),
    )


def heuristic_label(f):
    """Map features -> dominant 6-cat label. Rough; one vote of three."""
    cc = f["char_count"]
    wc = f["word_count"]
    taf = f["table_area_frac"]
    iaf = f["image_area_frac"]
    daf = f["drawing_area_frac"]
    tx = f["text_area_frac"]
    nt = f["n_tables"]
    nd = f["n_drawings"]
    content = f["content_frac"]

    reasons = []

    # Cover/Divider: very little text, little content overall
    if cc < 200 and content < 0.45 and nt == 0:
        # could be cover (image/logo + title) or blank divider
        if iaf > 0.5:
            return "Image/Photo", "low text, large image covers page"
        return "Cover/Divider", f"low text ({cc} ch), sparse content ({content})"

    # Image/Photo: dominated by raster image, little text
    if iaf >= 0.6 and cc < 400:
        return "Image/Photo", f"image covers {iaf} of page, text low"

    # Table: tables present covering meaningful area
    table_strong = nt >= 1 and taf >= 0.25
    # Chart/Diagram: lots of vector drawing area, modest text
    chart_strong = nd >= 40 and daf >= 0.25 and cc < 1500

    text_strong = cc >= 600 and tx >= 0.25

    strong = []
    if table_strong:
        strong.append("Table")
    if chart_strong:
        strong.append("Chart/Diagram")
    if text_strong:
        strong.append("Text")

    if len(strong) >= 2:
        return "Mixed", f"multiple strong signals: {strong}"
    if len(strong) == 1:
        return strong[0], f"single strong signal ({strong[0]})"

    # weak fallbacks
    if nt >= 1 and taf >= 0.12:
        return "Table", f"weak table signal taf={taf}"
    if nd >= 60 and daf >= 0.15:
        return "Chart/Diagram", f"weak vector signal nd={nd} daf={daf}"
    if cc >= 300:
        return "Text", f"text fallback cc={cc}"
    if iaf >= 0.3:
        return "Image/Photo", f"image fallback iaf={iaf}"
    return "Cover/Divider", f"fallback: cc={cc} content={content}"


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "Data"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "ground_truth/deterministic"
    os.makedirs(out_dir, exist_ok=True)
    pdfs = sorted(glob.glob(os.path.join(data_dir, "*.pdf")))
    summary = {}
    for pdf in pdfs:
        name = os.path.splitext(os.path.basename(pdf))[0]
        doc = fitz.open(pdf)
        pages = []
        for i in range(doc.page_count):
            page = doc[i]
            f = page_features(page)
            label, reason = heuristic_label(f)
            pages.append(dict(page=i + 1, det_label=label, reason=reason, **f))
        doc.close()
        out = os.path.join(out_dir, name + ".json")
        with open(out, "w") as fh:
            json.dump(dict(doc=name, n_pages=len(pages), pages=pages), fh, indent=2)
        # tally
        tally = {c: 0 for c in CATS}
        for p in pages:
            tally[p["det_label"]] += 1
        summary[name] = dict(n_pages=len(pages), tally=tally)
        print(f"{name}: {len(pages)} pages -> {tally}")
    with open(os.path.join(out_dir, "_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print("\nWrote per-doc JSON + _summary.json to", out_dir)


if __name__ == "__main__":
    main()
