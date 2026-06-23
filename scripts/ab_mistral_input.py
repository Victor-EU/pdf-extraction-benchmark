#!/usr/bin/env python3
"""Input A/B for Mistral OCR-4: rasterized PNG page vs born-digital single-page PDF.

Decides which input the canonical full-corpus run should use, the same way the Landing AI DPT-2
input choice was settled (ab_landingai_dpt2 -> PNG beat PDF-page by 7.2pp THERE; OCR-4 is a
different pipeline so we re-measure rather than assume). Both arms reduced identically via
mistral_common.reduce_page, so the only judged difference is input fidelity.

Stratified, chart-weighted sample across ALL THREE docs. Raw cached under ground_truth/mistral_ab/.
Usage: ./.venv-mistral/bin/python scripts/ab_mistral_input.py [limit]
Output: ground_truth/mistral_ab/{raw/*.json, extract.json}
"""
import os, sys, json, glob, collections
import mistral_common as M

RENDER = "ground_truth/render_full"
OUT = "ground_truth/mistral_ab"
# chart-weighted but spanning the categories where input fidelity could plausibly differ.
SEL = {"Text": 6, "Table": 6, "Mixed": 5, "Chart/Diagram": 5, "Cover/Divider": 1, "Image/Photo": 1}


def pdfs():
    return {os.path.splitext(os.path.basename(p))[0]: p for p in glob.glob("Data/*.pdf")}


def pick_pages():
    k = json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))["pages"]
    bycat = collections.defaultdict(list)
    for r in k:
        bycat[r["final_label"]].append((r["doc"], r["page"]))
    chosen = []
    for cat, n in SEL.items():
        items = sorted(bycat.get(cat, []))
        if not items:
            continue
        if n >= len(items):
            sel = items
        else:
            step = len(items) / n
            sel = [items[int(i * step)] for i in range(n)]
        chosen += [(d, p, cat) for (d, p) in sel]
    return sorted(set(chosen))


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    os.makedirs(os.path.join(OUT, "raw"), exist_ok=True)
    cl = M.client()
    P = pdfs()
    pages = pick_pages()
    if limit:
        pages = pages[:limit]
    print(f"OCR-4 input A/B over {len(pages)} pages (PNG vs born-digital PDF):")
    records = []
    for doc, page, cat in pages:
        png = os.path.join(RENDER, f"{doc}__p{page:04d}.png")
        row = {"doc": doc, "page": page, "cat": cat}
        for arm, mk_doc in (("png", lambda: {"type": "image_url", "image_url": M.png_datauri(png)}),
                            ("pdf", lambda: {"type": "document_url",
                                             "document_url": M.page_pdf_datauri(P[doc], page)})):
            rawp = os.path.join(OUT, "raw", f"{doc}__p{page:04d}__{arm}.json")
            if os.path.exists(rawp):
                resp = json.load(open(rawp))
            else:
                resp, wall = M.ocr_call(cl, mk_doc())
                resp["_wall"] = round(wall, 2)
                json.dump(resp, open(rawp, "w"))
            pg = (resp.get("pages") or [{}])[0]
            md, tables, figures = M.reduce_page(pg)
            row[f"{arm}_md"] = M.full_page_md(md, figures)   # body + figure descriptions, as judged
            row[f"{arm}_ntab"] = len(tables)
            row[f"{arm}_nfig"] = len(figures)
            row[f"{arm}_wall"] = resp.get("_wall")
        records.append(row)
        print(f"  {doc[:26]:<26} p{page:<4} {cat:<14} "
              f"png={len(row['png_md']):<6}({row['png_ntab']}t/{row['png_nfig']}f) "
              f"pdf={len(row['pdf_md']):<6}({row['pdf_ntab']}t/{row['pdf_nfig']}f)",
              flush=True)
    json.dump(records, open(os.path.join(OUT, "extract.json"), "w"), indent=2)
    print(f"\nWrote {len(records)} pages -> {OUT}/extract.json")


if __name__ == "__main__":
    main()
