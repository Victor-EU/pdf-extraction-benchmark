#!/usr/bin/env python3
"""Aggregate the spatial-relationship judge into a vendor RANKING and write SPATIAL_RANKING.md.

Per vendor, weighted by each page's spatial weight:
  - field   = field_value_binding   (over pages where field_present)
  - check   = checkbox_state        (over pages where checkbox_present)
  - cell    = table_cell_binding    (over pages where table_present)
  - SPATIAL = per-page composite (weighted mean of present types, W) aggregated over all pages.
"""
import json

W = {"field_value_binding": 1.0, "checkbox_state": 1.0, "table_cell_binding": 0.8}
COAUTHOR = {"gemini_flash", "gemini_flash_lite", "landingai"}  # GT co-authors -> upper bound (◆)
LABEL = {"gpt5_image": "gpt-5 (image)", "gpt5_file": "gpt-5 (file)",
         "gemini_flash": "Gemini 3.5 Flash", "gemini_flash_lite": "Gemini Flash-Lite",
         "landingai": "Landing AI (DPT-2)", "llamaparse": "LlamaParse",
         "pymupdf": "PyMuPDF", "tesseract": "Tesseract", "liteparse": "LiteParse",
         "mistral": "Mistral OCR 4"}
FAM = {"gpt-5": "results/_spatial_judging.json", "Gemini": "results/_spatial_judging_gemini.json"}


def composite(s):
    num = den = 0.0
    for k, pres in (("field_value_binding", "field_present"),
                    ("checkbox_state", "checkbox_present"),
                    ("table_cell_binding", "table_present")):
        if s.get(pres):
            num += s[k] * W[k]; den += W[k]
    return (num / den) if den else None


def aggregate(path):
    runs = json.load(open(path))
    vendors = sorted({v for r in runs for v in r.get("scores", {})})
    agg = {}
    for v in vendors:
        comp_n = comp_d = 0.0
        per = {"field_value_binding": [0.0, 0.0], "checkbox_state": [0.0, 0.0],
               "table_cell_binding": [0.0, 0.0]}  # [num, den] weighted by page spatial weight
        for r in runs:
            w = r.get("weight") or 0
            s = r.get("scores", {}).get(v)
            if not s or not w:
                continue
            c = composite(s)
            if c is not None:
                comp_n += c * w; comp_d += w
            for k, pres in (("field_value_binding", "field_present"),
                            ("checkbox_state", "checkbox_present"),
                            ("table_cell_binding", "table_present")):
                if s.get(pres):
                    per[k][0] += s[k] * w; per[k][1] += w
        agg[v] = {"spatial": comp_n / comp_d if comp_d else float("nan"),
                  "field": per["field_value_binding"][0] / per["field_value_binding"][1] if per["field_value_binding"][1] else None,
                  "check": per["checkbox_state"][0] / per["checkbox_state"][1] if per["checkbox_state"][1] else None,
                  "cell": per["table_cell_binding"][0] / per["table_cell_binding"][1] if per["table_cell_binding"][1] else None}
    return agg


def pct(x):
    return "–" if x is None else f"{x:.0f}%"


def main():
    fam = {name: aggregate(path) for name, path in FAM.items()}
    L = []; w = L.append
    w("# Spatial-relationship ranking — insurance forms (vendor vs ground truth)")
    w("")
    w("> **Why this metric.** These are FORMS: a value's meaning lives entirely in its 2-D position "
      "— which label it sits beside, which option a tick belongs to, which row×column a cell occupies. "
      "A parser that recovers every character but detaches it from its position has captured nothing "
      "usable. This ranking scores ONLY the spatial relationships (prose recall is ignored), split into "
      "the three that matter on these forms, judged blind by **both** a gpt-5 and a Gemini 3.5 Flash "
      "judge against `ground_truth/GROUND_TRUTH.md` (`scripts/score_spatial.py`).")
    w("")
    w("- **field** = field-label → value binding (value attached to the *correct* label)")
    w("- **check** = checkbox/radio state bound to the correct option (the most consequential, purely-spatial call)")
    w("- **cell** = table cell placed in the correct row×column")
    w("- **SPATIAL** = per-page composite (field & check weighted 1.0, cell 0.8), weighted by each page's spatial density")
    w("")
    w("> ◆ = ground-truth co-author (Gemini, and lightly the legacy Landing AI), so its scores are an "
      "**upper bound** and are **not ranked**. Cleanly graded: **gpt-5 (image), LlamaParse, PyMuPDF, "
      "Tesseract, LiteParse**. Landing AI is shown on its current **DPT-2** model. **n = 7 pages** — read the wide "
      "gaps as signal, the few-point gaps as noise.")
    w("")
    for name in FAM:
        ag = fam[name]
        clean = sorted([v for v in ag if v not in COAUTHOR], key=lambda v: -ag[v]["spatial"])
        co = sorted([v for v in ag if v in COAUTHOR], key=lambda v: -ag[v]["spatial"])
        w(f"## {name} judge")
        w("")
        w("| Rank | Vendor | **SPATIAL** | field | check | cell |")
        w("|---:|---|---:|---:|---:|---:|")
        for i, v in enumerate(clean, 1):
            a = ag[v]
            w(f"| {i} | {LABEL.get(v, v)} | **{pct(a['spatial'])}** | {pct(a['field'])} | {pct(a['check'])} | {pct(a['cell'])} |")
        for v in co:
            a = ag[v]
            w(f"| ◆ | {LABEL.get(v, v)} ◆ | {pct(a['spatial'])} | {pct(a['field'])} | {pct(a['check'])} | {pct(a['cell'])} |")
        w("")
    open("results/SPATIAL_RANKING.md", "w").write("\n".join(L) + "\n")
    print("wrote results/SPATIAL_RANKING.md\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
