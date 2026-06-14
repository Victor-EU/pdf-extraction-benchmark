#!/usr/bin/env python3
"""PyMuPDF heuristic page classifier — a candidate parsing solution.

PyMuPDF emits low-level structure (text / images / vector drawings / find_tables),
NOT semantic page categories. This builds a principled, first-principles classifier
on top of those features (NO tuning against the answer key) and times the parse so
we can report speed. Output: results/_pymupdf_solution.json [{doc,page,label,seconds,cost_usd}].

Category signatures used (reasoned, not fitted):
  Text          high char count + high text-area, no dominant table/chart/image
  Table         find_tables() hit covering real area  (axis-aligned grid, monochrome)
  Chart/Diagram vector-heavy: curves / diagonal lines / many fill colors / bar rects
  Image/Photo   raster image dominates AND it's a multi-image gallery (rare)
  Cover/Divider sparse text + (one big decorative image OR mostly blank)  [by function]
  Mixed         >=2 substantial signals coexist, none dominant
"""
import fitz, json, sys, os, time, glob

CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]
GRID = 64  # occupancy grid resolution for area-coverage (handles overlaps)


def cover_frac(rects, pr):
    """Fraction of page covered by a set of rects, via occupancy grid (union)."""
    if not rects:
        return 0.0
    W = pr.width or 1.0
    H = pr.height or 1.0
    cells = bytearray(GRID * GRID)
    for r in rects:
        x0 = max(0, min(GRID - 1, int((r.x0 - pr.x0) / W * GRID)))
        x1 = max(0, min(GRID - 1, int((r.x1 - pr.x0) / W * GRID)))
        y0 = max(0, min(GRID - 1, int((r.y0 - pr.y0) / H * GRID)))
        y1 = max(0, min(GRID - 1, int((r.y1 - pr.y0) / H * GRID)))
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        for gy in range(y0, y1 + 1):
            base = gy * GRID
            for gx in range(x0, x1 + 1):
                cells[base + gx] = 1
    return sum(cells) / (GRID * GRID)


def features(page):
    pr = page.rect
    text = page.get_text("text") or ""
    chars = len(text.strip())
    words = len(page.get_text("words"))
    # tables first, so we can separate cell-text from prose-text
    n_tables, table_rects = 0, []
    try:
        for tb in page.find_tables().tables:
            n_tables += 1
            if tb.bbox:
                table_rects.append(fitz.Rect(tb.bbox))
    except Exception:
        pass

    def in_table(r):
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        return any(t.x0 <= cx <= t.x1 and t.y0 <= cy <= t.y1 for t in table_rects)

    d = page.get_text("dict")
    text_rects, prose_rects, fonts = [], [], []
    prose_chars = 0
    for b in d.get("blocks", []):
        if b.get("type") == 0:
            for ln in b.get("lines", []):
                for sp in ln.get("spans", []):
                    txt = sp.get("text", "").strip()
                    if txt:
                        r = fitz.Rect(sp["bbox"])
                        text_rects.append(r)
                        fonts.append(sp.get("size", 0))
                        if not in_table(r):          # cell text != prose
                            prose_rects.append(r)
                            prose_chars += len(txt)
    img_rects = []
    for img in page.get_images(full=True):
        try:
            img_rects += [fitz.Rect(r) for r in page.get_image_rects(img[0])]
        except Exception:
            pass
    n_lines = n_diag = n_curves = n_rects = 0
    fills = set()
    draw_rects = []
    for dr in page.get_drawings():
        if dr.get("rect"):
            draw_rects.append(dr["rect"])
        f = dr.get("fill")
        if f:
            fills.add(tuple(round(x, 2) for x in f))
        for it in dr.get("items", []):
            op = it[0]
            if op == "l":
                p1, p2 = it[1], it[2]
                if abs(p1.x - p2.x) < 0.6 or abs(p1.y - p2.y) < 0.6:
                    n_lines += 1
                else:
                    n_diag += 1
            elif op == "c":
                n_curves += 1
            elif op in ("re", "qu"):
                n_rects += 1
    return dict(
        chars=chars, words=words, n_images=len(img_rects),
        prose_chars=prose_chars,
        prose_text_frac=cover_frac(prose_rects, pr),
        text_frac=cover_frac(text_rects, pr),
        image_frac=cover_frac(img_rects, pr),
        draw_frac=cover_frac(draw_rects, pr),
        table_frac=cover_frac(table_rects, pr),
        n_lines=n_lines, n_diag=n_diag, n_curves=n_curves, n_rects=n_rects,
        n_fills=len(fills), n_tables=n_tables,
        avg_font=(sum(fonts) / len(fonts) if fonts else 0),
    )


def classify(f):
    chars = f["chars"]
    ptf, ptc = f["prose_text_frac"], f["prose_chars"]   # prose only (cell text excluded)
    imf, dgf = f["image_frac"], f["draw_frac"]
    taf, nt = f["table_frac"], f["n_tables"]
    # chart-ness: curves + diagonals + color variety + bar-like filled rects
    chartiness = f["n_curves"] + f["n_diag"] + max(0, f["n_fills"] - 3) * 4
    content = min(ptf + imf + dgf + taf, 1.0)

    # 1) essentially blank -> divider
    if chars < 60 and imf < 0.15 and dgf < 0.15 and nt == 0:
        return "Cover/Divider"
    # 2) big image + little text -> photo cover (by function) or gallery
    if imf >= 0.40 and chars < 320 and nt == 0:
        return "Image/Photo" if f["n_images"] >= 4 else "Cover/Divider"

    # substantial signals (Text uses PROSE only; table cell text doesn't count)
    text_strong = ptc >= 450 and ptf >= 0.28
    table_strong = nt >= 1 and taf >= 0.16
    chart_strong = chartiness >= 45 and dgf >= 0.18 and ptc < 1600
    img_strong = imf >= 0.32

    strong = [k for k, v in [("Text", text_strong), ("Table", table_strong),
                             ("Chart/Diagram", chart_strong), ("Image/Photo", img_strong)] if v]

    # 3) sparse text divider (no strong content signal)
    if chars < 200 and content < 0.45 and not strong:
        return "Cover/Divider"

    # 4) Mixed only when 2+ strong signals genuinely coexist
    if len(strong) >= 2:
        return "Mixed"
    # 5) single dominant signal
    if len(strong) == 1:
        return strong[0]

    # 6) weak fallbacks (priority: table > chart > text > image > divider)
    if nt >= 1 and taf >= 0.08:
        return "Table"
    if chartiness >= 20 and dgf >= 0.10 and dgf >= imf:
        return "Chart/Diagram"
    if ptc >= 300:
        return "Text"
    if imf >= 0.18:
        return "Cover/Divider"
    return "Cover/Divider"


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "Data"
    out = sys.argv[2] if len(sys.argv) > 2 else "results/_pymupdf_solution.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sol, feats = [], []
    for pdf in sorted(glob.glob(os.path.join(data_dir, "*.pdf"))):
        name = os.path.splitext(os.path.basename(pdf))[0]
        doc = fitz.open(pdf)
        npages = doc.page_count
        for i in range(npages):
            t0 = time.perf_counter()
            f = features(doc[i])
            label = classify(f)
            dt = time.perf_counter() - t0
            sol.append(dict(doc=name, page=i + 1, label=label,
                            seconds=round(dt, 4), cost_usd=0.0))
            feats.append(dict(doc=name, page=i + 1, label=label, **f))
        doc.close()
        print(f"{name}: {npages} pages")
    json.dump(sol, open(out, "w"), indent=2)
    json.dump(feats, open("results/_pymupdf_features.json", "w"), indent=2)
    tot = sum(r["seconds"] for r in sol)
    print(f"\n{len(sol)} pages classified in {tot:.1f}s total "
          f"({1000*tot/len(sol):.1f} ms/page) -> {out}")


if __name__ == "__main__":
    main()
