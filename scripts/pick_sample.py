#!/usr/bin/env python3
"""Pick a stratified, diversity-maximizing sample and render pages to PNG.

For each doc, target N pages, allocated across the 6 heuristic categories so the
sample exercises tables/charts/images/covers (not just easy text). Within each
category, pick evenly-spaced pages by page number. Render selected pages at DPI.
"""
import sys, os, json, glob, math
import fitz

CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]


def evenly(items, k):
    """Pick k evenly-spaced elements from a list (preserving order)."""
    if k <= 0 or not items:
        return []
    if k >= len(items):
        return list(items)
    idx = [round(i * (len(items) - 1) / (k - 1)) for i in range(k)]
    seen, out = set(), []
    for j in idx:
        if j not in seen:
            seen.add(j)
            out.append(items[j])
    # backfill if rounding collided
    i = 0
    while len(out) < k and i < len(items):
        if items[i] not in out:
            out.append(items[i])
        i += 1
    return sorted(out)


def allocate(present_counts, total):
    """Allocate `total` slots across present categories: floor of proportional
    but guarantee >=2 per present category where possible, cap by availability."""
    present = {c: n for c, n in present_counts.items() if n > 0}
    if not present:
        return {}
    alloc = {}
    # base: 2 each (or available)
    for c, n in present.items():
        alloc[c] = min(2, n)
    used = sum(alloc.values())
    remaining = total - used
    if remaining > 0:
        # distribute remainder by category size
        order = sorted(present.items(), key=lambda kv: -kv[1])
        i = 0
        while remaining > 0:
            c, n = order[i % len(order)]
            if alloc[c] < n:
                alloc[c] += 1
                remaining -= 1
            elif all(alloc[cc] >= present[cc] for cc in present):
                break
            i += 1
    return alloc


def main():
    det_dir = sys.argv[1] if len(sys.argv) > 1 else "ground_truth/deterministic"
    data_dir = sys.argv[2] if len(sys.argv) > 2 else "Data"
    render_dir = sys.argv[3] if len(sys.argv) > 3 else "ground_truth/render"
    per_doc = int(sys.argv[4]) if len(sys.argv) > 4 else 20
    dpi = int(sys.argv[5]) if len(sys.argv) > 5 else 150
    os.makedirs(render_dir, exist_ok=True)

    manifest = []
    for det_json in sorted(glob.glob(os.path.join(det_dir, "*.json"))):
        if os.path.basename(det_json).startswith("_"):
            continue
        with open(det_json) as fh:
            d = json.load(fh)
        name = d["doc"]
        pages = d["pages"]
        by_cat = {c: [] for c in CATS}
        det_of = {}
        for p in pages:
            by_cat[p["det_label"]].append(p["page"])
            det_of[p["page"]] = p["det_label"]
        counts = {c: len(by_cat[c]) for c in CATS}
        alloc = allocate(counts, per_doc)
        chosen = []
        for c, k in alloc.items():
            chosen += evenly(sorted(by_cat[c]), k)
        chosen = sorted(set(chosen))
        # render
        pdf = os.path.join(data_dir, name + ".pdf")
        doc = fitz.open(pdf)
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        for pg in chosen:
            page = doc[pg - 1]
            pix = page.get_pixmap(matrix=mat)
            fn = f"{name}__p{pg:04d}.png"
            pix.save(os.path.join(render_dir, fn))
            manifest.append(dict(doc=name, page=pg, det_label=det_of[pg], png=fn))
        doc.close()
        print(f"{name}: alloc={alloc} -> {len(chosen)} pages")

    with open(os.path.join(render_dir, "_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"\nTotal sample pages: {len(manifest)} -> manifest at {render_dir}/_manifest.json")


if __name__ == "__main__":
    main()
