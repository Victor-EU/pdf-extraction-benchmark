#!/usr/bin/env python3
"""Tesseract OCR heuristic page classifier — a candidate parsing solution.

Tesseract is a pure OCR engine: image -> text + word boxes + confidences. It has
NO native table/figure detection and no access to the PDF's vector structure (it
works on rasterized pixels). So this classifier can only reason about TEXT AMOUNT,
TEXT COVERAGE, WORD-BOX ALIGNMENT (a table proxy), and WHERE TEXT ISN'T (non-text
regions). Thresholds set from first principles, NOT fitted to the answer key.

Outputs results/_tesseract_solution.json [{doc,page,label,seconds,cost_usd}].
"""
import os, sys, json, time, glob
from multiprocessing import Pool
import pytesseract
from PIL import Image

GRID = 64
CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]


def cover_frac(boxes, W, H):
    if not boxes:
        return 0.0
    cells = bytearray(GRID * GRID)
    for (l, t, w, h) in boxes:
        x0 = max(0, min(GRID - 1, int(l / W * GRID)))
        x1 = max(0, min(GRID - 1, int((l + w) / W * GRID)))
        y0 = max(0, min(GRID - 1, int(t / H * GRID)))
        y1 = max(0, min(GRID - 1, int((t + h) / H * GRID)))
        for gy in range(y0, y1 + 1):
            base = gy * GRID
            for gx in range(x0, x1 + 1):
                cells[base + gx] = 1
    return sum(cells) / (GRID * GRID)


def features_from_tsv(data, W, H):
    n = len(data["text"])
    words = []   # (left, top, width, height)
    lines = set()
    confs = []
    for i in range(n):
        txt = (data["text"][i] or "").strip()
        try:
            conf = float(data["conf"][i])
        except Exception:
            conf = -1
        if txt and conf >= 30:
            words.append((data["left"][i], data["top"][i], data["width"][i], data["height"][i]))
            lines.add((data["block_num"][i], data["par_num"][i], data["line_num"][i]))
            confs.append(conf)
    n_words = len(words)
    n_lines = len(lines)
    text_cov = cover_frac(words, W, H)
    chars = sum(len(data["text"][i].strip()) for i in range(n)
                if data["text"][i] and data["text"][i].strip())

    # column-GAP table proxy: a table has >=2 internal vertical whitespace gaps
    # (>=3 columns). 1-col prose -> 0 internal gaps; 2-col prose -> 1. Robust vs
    # the naive left-edge alignment that false-fires on justified prose.
    n_colgaps = 0
    if words:
        xs0 = min(w[0] for w in words)
        xs1 = max(w[0] + w[2] for w in words)
        region_w = max(1.0, xs1 - xs0)
        NB = 50
        crossings = [0] * NB
        for (l, t, w, h) in words:
            b0 = max(0, int((l - xs0) / region_w * NB))
            b1 = min(NB - 1, int((l + w - xs0) / region_w * NB))
            for b in range(b0, b1 + 1):
                crossings[b] += 1
        maxc = max(crossings) or 1
        occ = [c / maxc for c in crossings]
        thresh = 0.06
        in_gap = False
        seen_content = False
        for b in range(NB):
            if occ[b] >= thresh:
                if in_gap and seen_content:
                    n_colgaps += 1   # closed an internal gap
                in_gap = False
                seen_content = True
            elif seen_content:
                in_gap = True

    return dict(n_words=n_words, n_lines=n_lines, chars=chars,
                text_cov=round(text_cov, 3), nontext_frac=round(1 - text_cov, 3),
                n_colgaps=n_colgaps,
                mean_conf=round(sum(confs) / len(confs), 1) if confs else 0)


def classify(f):
    nw, cov, nt = f["n_words"], f["text_cov"], f["nontext_frac"]
    gaps, nlines = f["n_colgaps"], f["n_lines"]

    # 1) almost no text -> sparse page (OCR can't tell photo from blank -> divider)
    if nw < 12:
        return "Cover/Divider"
    # 2) clear multi-column grid (>=2 internal gaps) across several rows -> Table
    if gaps >= 2 and nlines >= 6 and cov >= 0.10:
        return "Table"
    # 3) dense text body
    text_strong = nw >= 110 and cov >= 0.28
    big_nontext = nt >= 0.62
    # text + a large non-text region (chart/photo block) coexisting -> Mixed
    if text_strong and big_nontext:
        return "Mixed"
    if text_strong:
        return "Text"
    # 4) moderate scattered text over a large non-text region -> Chart/Diagram
    #    (OCR can't tell chart from photo; Image/Photo is rare -> default Chart/Diagram)
    if nw >= 22 and big_nontext:
        return "Chart/Diagram"
    # 5) some uniform text, not dense -> Text
    if nw >= 55 and cov >= 0.15:
        return "Text"
    # 6) little text, little structure -> divider
    if nw < 30:
        return "Cover/Divider"
    return "Chart/Diagram"


def work(item):
    doc, page, png, path = item
    try:
        img = Image.open(path)
        W, H = img.size
        t0 = time.perf_counter()
        data = pytesseract.image_to_data(img, config="--psm 3",
                                         output_type=pytesseract.Output.DICT)
        dt = time.perf_counter() - t0
        f = features_from_tsv(data, W, H)
        label = classify(f)
        return dict(doc=doc, page=page, label=label, seconds=round(dt, 3),
                    cost_usd=0.0, **f)
    except Exception as e:
        return dict(doc=doc, page=page, label="Cover/Divider", seconds=0.0,
                    cost_usd=0.0, error=str(e))


def main():
    render = sys.argv[1] if len(sys.argv) > 1 else "ground_truth/render_full"
    out = sys.argv[2] if len(sys.argv) > 2 else "results/_tesseract_solution.json"
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    os.makedirs(os.path.dirname(out), exist_ok=True)
    manifest = json.load(open(os.path.join(render, "_manifest.json")))
    items = [(m["doc"], m["page"], m["png"], os.path.join(render, m["png"])) for m in manifest]
    t0 = time.time()
    with Pool(workers) as p:
        results = p.map(work, items)
    results.sort(key=lambda r: (r["doc"], r["page"]))
    sol = [{"doc": r["doc"], "page": r["page"], "label": r["label"],
            "seconds": r["seconds"], "cost_usd": 0.0} for r in results]
    json.dump(sol, open(out, "w"), indent=2)
    json.dump(results, open("results/_tesseract_features.json", "w"), indent=2)
    errs = [r for r in results if r.get("error")]
    secs = [r["seconds"] for r in results if r["seconds"]]
    print(f"{len(results)} pages OCR+classified in {time.time()-t0:.0f}s wall "
          f"({workers} workers); per-page OCR mean {sum(secs)/len(secs):.2f}s; errors {len(errs)}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
