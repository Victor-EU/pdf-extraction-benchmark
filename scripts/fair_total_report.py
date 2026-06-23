#!/usr/bin/env python3
"""Assemble the document-level FAIR TOTAL from results/_fair_total_judging.json and write
results/FAIR_TOTAL.md — the single density-weighted "total information captured" score per vendor,
plus a paraphrase-tolerant per-category breakdown and a fidelity (unsupported-claims) column."""
import json
from collections import defaultdict

VEND_LABEL = {
    "gpt5_image": "gpt-5 (image) ◆", "gpt5_file": "gpt-5 (file) ◆",
    "gemini_flash": "Gemini 3.5 Flash", "gemini_flash_lite": "Gemini 3.1 Flash-Lite",
    "landingai": "Landing AI", "llamaparse": "LlamaParse",
    "pymupdf": "PyMuPDF", "tesseract": "Tesseract", "liteparse": "LiteParse",
}
ORDER = ["landingai", "gemini_flash", "gpt5_image", "gpt5_file", "gemini_flash_lite",
         "llamaparse", "pymupdf", "tesseract", "liteparse"]
REF = {"gpt5_image", "gpt5_file"}  # built the GT — upper bound, not comparable


def pct(x):
    return f"{100*x:.0f}%" if x is not None else "–"


def _accum(fj, key):
    num = defaultdict(float); den = defaultdict(float)
    rec_simple = defaultdict(list); unsup = defaultdict(list)
    cat_num = defaultdict(lambda: defaultdict(float)); cat_den = defaultdict(lambda: defaultdict(float))
    npages = 0; err = 0
    for r in fj:
        if r.get("error"):
            err += 1; continue
        npages += 1
        w = r.get("weight", 1)
        cat = key.get((r["doc"], r["page"]), "?")
        for vd, s in r.get("scores", {}).items():
            ir = s.get("info_recall")
            if ir is None: continue
            num[vd] += ir * w; den[vd] += w
            cat_num[vd][cat] += ir * w; cat_den[vd][cat] += w
            rec_simple[vd].append(ir)
            if s.get("unsupported") is not None: unsup[vd].append(s["unsupported"])
    return dict(num=num, den=den, rec_simple=rec_simple, unsup=unsup,
                cat_num=cat_num, cat_den=cat_den, npages=npages, err=err)


def main():
    import os
    fj = json.load(open(os.environ.get("FT_IN", "results/_fair_total_judging.json")))             # structure-aware
    cj = json.load(open(os.environ.get("FT_CONTENT", "results/_fair_total_judging_content.json")))  # diagnostic
    key = {(e["doc"], e["page"]): e["final_label"]
           for e in json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))["pages"]}

    S = _accum(fj, key); C = _accum(cj, key)
    npages = S["npages"]; err = S["err"]

    def ft(A, vd): return A["num"][vd] / A["den"][vd] / 100 if A["den"][vd] else None
    def mean(xs): return sum(xs) / len(xs) / 100 if xs else None
    def catft(A, vd, c): return A["cat_num"][vd][c] / A["cat_den"][vd][c] / 100 if A["cat_den"][vd][c] else None

    order = sorted(ORDER, key=lambda vd: (vd in REF, -(ft(S, vd) or 0)))  # rank by structure-aware total

    L = []; w = L.append
    w("# Fair Total — STRUCTURE-AWARE document-level information capture")
    w("")
    w("> **Scores are structure-aware as of 2026-06-14.** A value counts as captured only if its "
      "**binding is recoverable** — which row/column/series/node/entity it belongs to — because on "
      "finance / M&A / consulting documents a number bound to the wrong row is an *active downstream "
      "error*, worse than an omission. Correct structure described in prose still earns full credit "
      "(not a formatting test); on unstructured pages (prose, dividers) the metric reduces to ordinary "
      "content recall. The prior **content-recall** rubric (information present, ignoring binding) is "
      "preserved as a diagnostic column and in `*_content.json`. See "
      "[`../STRUCTURE_AWARE_SCORING.md`](../STRUCTURE_AWARE_SCORING.md).")
    w("")
    w(f"Each vendor's full {npages}-page extraction was diffed, page by page, against a ground-truth "
      "markdown transcription (`ground_truth/GROUND_TRUTH.md`) by a blind gpt-5 judge that **credits "
      "equivalent phrasing** but requires the correct bindings to be recoverable.")
    w("")
    w("**Fair total** = Σ(info_recall × page_info_weight) ÷ Σ(page_info_weight) over all pages — a true "
      "ratio of *correctly-bound information captured to total information present*, weighted by how much "
      "real content each page holds. It is NOT an average of arbitrary dimension scores.")
    w("")
    w("> ◆ gpt-5 built the ground truth (same model family), so its two rows are an **upper bound by "
      "construction** — reported for context, not directly comparable. Every other vendor is graded cleanly.")
    w("")
    w("## The fair total")
    w("")
    w("| Vendor | **Fair total** (structure-aware) | Content recall (diagnostic) | Structure gap | Unsupported (fidelity) |")
    w("|---|---:|---:|---:|---:|")
    for vd in order:
        s = ft(S, vd); c = ft(C, vd)
        gap = f"−{100*(c-s):.0f}" if (s is not None and c is not None) else "–"
        w(f"| {VEND_LABEL[vd]} | **{pct(s)}** | {pct(c)} | {gap} | {pct(mean(S['unsup'][vd]))} |")
    w("")
    w("> **Structure gap** = content recall − structure-aware fair total = the share of a vendor's "
      "apparent capture that does NOT survive a binding check. The largest gaps (LiteParse −18, PyMuPDF, "
      "Tesseract) mark tools that recover characters but lose structure; a small gap marks "
      "downstream-usable output. LiteParse's gap is the widest of all: its heuristic markdown emits "
      "table/heading *shapes* (table-presence 81%, well above PyMuPDF's 57%) but on dense multi-column "
      "finance pages its grid projection merges adjacent columns into a jumble whose bindings the judge "
      "cannot recover — so the table-shaped output is not rewarded, and it scores *below* PyMuPDF's "
      "honest flat dump (62 vs 68). **Unsupported** now counts actively wrong bindings (a value under the "
      "wrong key) as contradictions.")
    w("")
    w("## Fair total by page category (structure-aware)")
    w("")
    CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]
    w("| Vendor | " + " | ".join(c.split("/")[0] for c in CATS) + " |")
    w("|---|" + "---:|" * len(CATS))
    for vd in order:
        w(f"| {VEND_LABEL[vd]} | " + " | ".join(pct(catft(S, vd, c)) for c in CATS) + " |")
    w("")
    if err:
        w(f"> {err} page(s) failed judging and are excluded.")
        w("")
    open("results/FAIR_TOTAL.md", "w").write("\n".join(L) + "\n")
    print("wrote results/FAIR_TOTAL.md\n")
    print("\n".join(L[:18]))


if __name__ == "__main__":
    main()
