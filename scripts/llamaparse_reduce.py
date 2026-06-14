#!/usr/bin/env python3
"""Reduce LlamaParse raw per-page output to a dominant 6-category label.

LlamaParse (accurate mode) structurally types regions as text/heading, table (with bBox,
csv), and raster images (with bBox; includes tiny footer logos -> filtered + deduped).
It has NO chart/diagram type in any mode (the `charts` array is empty even in agentic
mode; charts get absorbed into table/text), so Chart/Diagram is not directly recoverable
structurally — those pages fall to whichever of text/table/image dominates.

Thresholds mirror the Landing AI reducer (scripts/landingai_pass.py) from first-principles
feature semantics, NOT fitted to the answer key. Same fairness discipline as PyMuPDF.
Writes results/_llamaparse_solution.json and results/_llamaparse_full.json.
"""
import os, sys, json, glob
from collections import Counter

DOCS = {
    "20190308_Projet_Alpha_Restitution": 156,
    "IAR_FY25_EN": 310,
    "SOTER - Company Presentation - vFF": 133,
}
# LlamaParse emits a full-page background raster on EVERY slide of these born-digital
# decks (big_img==1.0 on all 599 pages), so the `images` field carries no photo/cover
# signal and is dropped entirely. Classification uses text vs table region area only.
COVER_TEXT = 0.12     # sparse page: little real text...
COVER_TABLE = 0.10    # ...and essentially no table structure
R_TABLE = 3.0         # table_a/text_a above this = table-dominant (captures charts-as-tables)
R_TEXT = 0.7          # ...below this = text-dominant; between = Mixed
TABLE_FLOOR = 0.70    # very large table area alone => Table even if text also present


def norm_area(b, W, H):
    try:
        return max(0.0, float(b["w"])) * max(0.0, float(b["h"])) / (W * H)
    except Exception:
        return 0.0


def reduce_page(p):
    W = float(p.get("width") or 1) or 1
    H = float(p.get("height") or 1) or 1
    text_a = table_a = 0.0
    n_text = n_table = 0
    for it in p.get("items", []):
        t = it.get("type")
        b = it.get("bBox")
        a = norm_area(b, W, H) if b else 0.0
        if t == "table":
            table_a += a; n_table += 1
        elif t in ("text", "heading"):
            text_a += a; n_text += 1

    detail = dict(text=round(text_a, 3), table=round(table_a, 3),
                  n_text=n_text, n_table=n_table, conf=p.get("confidence"))

    # 1) Cover/Divider — sparse page: little text, no table structure
    if text_a < COVER_TEXT and table_a < COVER_TABLE:
        return "Cover/Divider", detail

    # 2) text vs table ratio (charts are parsed AS tables -> land in Table, unavoidable)
    r = table_a / (text_a + 1e-6)
    if table_a >= TABLE_FLOOR or r >= R_TABLE:
        return "Table", detail
    if r <= R_TEXT:
        return "Text", detail
    # 3) both substantial, neither dominant
    return "Mixed", detail


def main():
    raw_dir = os.environ.get("LP_RAW_DIR", "ground_truth/llamaparse/raw")
    suffix = os.environ.get("LP_OUT_SUFFIX", "")  # e.g. "_agentic"
    raw = {}
    for doc in DOCS:
        f = f"{raw_dir}/{doc}.json"
        raw[doc] = json.load(open(f))

    sol, full = [], []
    walls = {d: raw[d].get("_wall_s") for d in DOCS}
    per_page_secs = {d: (walls[d] / DOCS[d] if walls[d] else None) for d in DOCS}
    total_credits = sum((raw[d].get("job_metadata", {}) or {}).get("credits_used", 0) or 0 for d in DOCS)

    for doc in DOCS:
        pages = raw[doc]["pages"]
        for p in pages:
            page_no = p["page"]  # 1-indexed within doc, matches our key
            label, detail = reduce_page(p)
            sol.append({"doc": doc, "page": page_no, "label": label,
                        "seconds": round(per_page_secs[doc], 3) if per_page_secs[doc] else None,
                        "cost_usd": 0.0})
            full.append({"doc": doc, "page": page_no, "label": label, **detail})

    sol.sort(key=lambda r: (r["doc"], r["page"]))
    full.sort(key=lambda r: (r["doc"], r["page"]))
    json.dump(sol, open(f"results/_llamaparse{suffix}_solution.json", "w"), indent=2)
    json.dump(full, open(f"results/_llamaparse{suffix}_full.json", "w"), indent=2)
    dist = Counter(r["label"] for r in sol)
    print("pages:", len(sol), "| credits:", total_credits,
          "| total wall:", round(sum(w for w in walls.values() if w), 0), "s")
    print("per-page mean:", round(sum(w for w in walls.values() if w) / len(sol), 3), "s")
    print("distribution:", dict(dist))


if __name__ == "__main__":
    main()
