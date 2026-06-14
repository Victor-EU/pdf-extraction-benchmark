#!/usr/bin/env python3
"""Render the deterministic validator (results/_deterministic_scores.json) into
results/DETERMINISTIC_VALIDATION.md + the disagreement worklist results/_deterministic_disagreements.json.

Run after deterministic_validate.py.
"""
import json
from statistics import mean, median

VENDORS = ["gemini_flash", "gpt5_image", "landingai", "llamaparse", "pymupdf", "tesseract"]
LABEL = {"gpt5_image": "gpt5_image ◆"}        # twin-bias upper bound (mirrors fair_total report)
# A measurement bug is VENDOR-SPECIFIC (the vendor_md ## split hit only LandingAI); a metric
# blind spot (non-numeric matrix) moves ALL vendors on a page together. So flag a vendor whose
# deterministic-vs-judge gap is an OUTLIER vs its peers on the SAME page, not the raw gap — this
# suppresses page-wide blind spots and isolates the bug signature.
FLAG_THRESH = 35                               # |vendor gap − page-median gap|


def avg(rows, f):
    vals = [r[f] for r in rows if r.get(f) is not None]
    return 100 * mean(vals) if vals else None


def avg_judge(rows, f):
    vals = [r[f] for r in rows if r.get(f) is not None]
    return mean(vals) if vals else None


def fmt(x):
    return f"{x:.0f}" if x is not None else "—"


def main():
    rows = json.load(open("results/_deterministic_scores.json"))
    by = {v: [r for r in rows if r["v"] == v] for v in VENDORS}

    def cat(rows, cats, gated=False):
        return [r for r in rows if r["cat"] in cats and (r["gated"] if gated else True)]

    L = []
    L.append("# Deterministic validator — zero-LLM cross-check on the headline (2026-06-14)\n")
    L.append("A reproducible, model-free triangulation of the LLM fair-total judge. It does **not** "
             "replace the judge; it corroborates the parts that are mechanically checkable on this "
             "born-digital corpus (printed numbers are an exact oracle) and flags where judge and "
             "oracle disagree. Scope and limits established in `POC_DETERMINISTIC_SCORING.md`.\n")
    L.append("Reproduce: `python3 scripts/deterministic_validate.py && python3 scripts/deterministic_report.py`\n")

    # ---- Job 1: tiering corroboration on TABLE pages ----
    L.append("\n## 1. Tiering corroboration — TABLE pages (gated, no LLM)\n")
    L.append("The **structure tax** = numeric_recall − binding_recall: numbers that are present but "
             "lost their row/series binding. `numeric_recall` saturates and cannot separate the "
             "text-dumper from the leaders; the structure tax does, and it tiers like the judge.\n")
    L.append("| vendor | numeric_recall | binding_recall | **structure tax** | judge_struct |")
    L.append("|---|---:|---:|---:|---:|")
    tbl = {v: cat(by[v], {"Table"}, gated=True) for v in VENDORS}
    tier = sorted(VENDORS, key=lambda v: -(avg(tbl[v], "binding_recall") or 0))
    for v in tier:
        r = tbl[v]
        nr, br = avg(r, "numeric_recall"), avg(r, "binding_recall")
        js = avg_judge(r, "judge_struct")
        tax = (nr - br) if (nr is not None and br is not None) else None
        L.append(f"| {LABEL.get(v, v)} | {fmt(nr)} | {fmt(br)} | **{fmt(tax)}** | {fmt(js)} |")
    L.append("\n*Read the structure tax inversely against judge_struct: low tax ↔ high judge "
             "(structure preserved); high tax ↔ low judge (structure destroyed). This reproduces "
             "the LandingAI-above-PyMuPDF ordering and the PyMuPDF/Tesseract collapse that "
             "numeric_recall alone (all ~98 except Tesseract) is blind to.*\n")

    # ---- Job 1b: TEXT diagnostic (confounded) ----
    L.append("\n### 1b. TEXT pages — diagnostic only (deterministic signal is confounded)\n")
    L.append("Shown for honesty, **not** used for corroboration. On prose, binding_recall diverges "
             "from the judge in both directions: Tesseract's OCR mangles label tokens so same-line "
             "matching fails (binding ≪ judge), while PyMuPDF's reading-order errors are invisible "
             "to a per-line check (binding ≫ judge). Tables are the clean cut.\n")
    L.append("| vendor | numeric_recall | binding_recall | judge_struct |")
    L.append("|---|---:|---:|---:|")
    for v in VENDORS:
        r = cat(by[v], {"Text"}, gated=True)
        L.append(f"| {LABEL.get(v, v)} | {fmt(avg(r,'numeric_recall'))} | "
                 f"{fmt(avg(r,'binding_recall'))} | {fmt(avg_judge(r,'judge_struct'))} |")

    # ---- Job 2: numeric-fidelity floor ----
    L.append("\n## 2. Numeric-fidelity floor — all number-bearing pages (oracle lower bound)\n")
    L.append("Fraction of the GT's **printed numbers** each vendor reproduces anywhere, by exact "
             "normalized match. Exact match never over-credits, and formatting variants can only "
             "*miss*, so this is a conservative **lower bound** on numeric capture. Tesseract's OCR "
             "floor is the only clear separation here — binding (job 1) is what de-saturates the rest.\n")
    L.append("| vendor | numeric floor (≥) |")
    L.append("|---|---:|")
    for v in sorted(VENDORS, key=lambda v: -(avg(by[v], "numeric_recall") or 0)):
        L.append(f"| {LABEL.get(v, v)} | {fmt(avg(by[v], 'numeric_recall'))}% |")

    # ---- Job 3: disagreement worklist — vendor outliers on gated table pages ----
    # group gated table rows by page; a vendor is flagged if its gap deviates from the page median.
    bypage = {}
    for r in rows:
        if r["cat"] != "Table" or not r["gated"]:
            continue
        if r["binding_recall"] is None or r["judge_struct"] is None:
            continue
        bypage.setdefault((r["doc"], r["page"]), []).append(r)
    flags = []
    for (doc, page), prs in bypage.items():
        for r in prs:
            r["gap"] = r["binding_recall"] * 100 - r["judge_struct"]
        med = median(r["gap"] for r in prs)
        for r in prs:
            anom = r["gap"] - med
            if abs(anom) >= FLAG_THRESH:
                flags.append({"v": r["v"], "doc": doc, "page": page,
                              "binding_recall": r["binding_recall"], "judge_struct": r["judge_struct"],
                              "gap": round(r["gap"], 1), "page_median_gap": round(med, 1),
                              "anomaly": round(anom, 1)})
    flags.sort(key=lambda r: -abs(r["anomaly"]))
    json.dump(flags, open("results/_deterministic_disagreements.json", "w"), indent=2)

    L.append(f"\n## 3. Judge-disagreement worklist — vendor outliers, gated TABLE pages\n")
    L.append(f"{len(flags)} vendor-page(s) where one vendor's deterministic-vs-judge gap is an "
             f"outlier (|gap − page median| ≥ {FLAG_THRESH}) vs its peers on the same page — the bug "
             "signature, since a real measurement bug is vendor-specific while a metric blind spot "
             "(e.g. a flattened feature matrix) moves all vendors together and cancels in the "
             "page median. **anomaly > 0**: this vendor scores far higher deterministically than "
             "the judge credits, vs peers — judge may under-score it, its structure may be "
             "non-numeric, OR its bindings are actively WRONG in a way same-line matching can't see "
             "(e.g. a header/body column-count mismatch shifts every value one column — real catch: "
             "Alpha p87 LandingAI, bind 98 / judge 20). **anomaly < 0**: deterministic says this "
             "vendor is far worse than the judge does, vs "
             "peers (parser/harness may be dropping its content — this is how the vendor_md `##` "
             "split was caught). Full list: `results/_deterministic_disagreements.json`.\n")
    if flags:
        L.append("| vendor | doc/page | bind | judge | gap | page-median | **anomaly** |")
        L.append("|---|---|---:|---:|---:|---:|---:|")
        for r in flags[:15]:
            dp = f"{r['doc'][:26]} p{r['page']}"
            L.append(f"| {r['v']} | {dp} | {r['binding_recall']*100:.0f} | {r['judge_struct']} | "
                     f"{r['gap']:+.0f} | {r['page_median_gap']:+.0f} | **{r['anomaly']:+.0f}** |")
    else:
        L.append("*No vendor outlier exceeds the threshold — deterministic and judge agree across "
                 "the gated table corpus.*")

    L.append("\n---\n*Generated by `scripts/deterministic_report.py` from "
             "`results/_deterministic_scores.json`. Limits: numeric-binding only — blind to "
             "charts (serialization/paraphrase), diagrams, and non-numeric tables, which remain "
             "the blind LLM judge's domain.*")

    open("results/DETERMINISTIC_VALIDATION.md", "w").write("\n".join(L) + "\n")
    print(f"-> results/DETERMINISTIC_VALIDATION.md ({len(flags)} disagreements flagged)")


if __name__ == "__main__":
    main()
