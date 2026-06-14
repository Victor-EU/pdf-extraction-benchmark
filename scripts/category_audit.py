#!/usr/bin/env python3
"""Per-category audit of the fair-total judging (v2 corrected GT).

Goes beyond the single FAIR_TOTAL.md category table to answer "which vendor is good at
what" defensibly:
  1. Per-category fair total + mean recall + n (sample size) + unsupported (fidelity).
  2. Category x document cross-tab — exposes the category/doc confound (Tables live in the
     annual report; Charts in the decks), so a category win isn't just a doc-mix artifact.
  3. Per-category vendor ranking + the gap to the runner-up (is the lead real or noise).
  4. Worklist of highest-divergence pages per category (max - min recall across clean
     vendors) — the pages to read GT-vs-vendor by hand to confirm the score is genuine.

Output: results/CATEGORY_AUDIT.md  + prints the divergence worklist.
"""
import json, os
from collections import defaultdict

VEND_LABEL = {
    "gemini_flash": "Gemini 3.5 Flash", "gemini_flash_lite": "Gemini 3.1 Flash-Lite",
    "landingai": "Landing AI", "pymupdf": "PyMuPDF", "llamaparse": "LlamaParse",
    "tesseract": "Tesseract", "gpt5_image": "gpt-5 (image) ◆", "gpt5_file": "gpt-5 (file) ◆",
}
CLEAN = ["gemini_flash", "gemini_flash_lite", "landingai", "pymupdf", "llamaparse", "tesseract"]
ALL = CLEAN + ["gpt5_image", "gpt5_file"]
CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]
DOC_SHORT = {"IAR_FY25_EN": "AnnualRpt", "20190308_Projet_Alpha_Restitution": "Alpha-deck",
             "SOTER - Company Presentation - vFF": "SOTER-deck"}


def load():
    key = {(e["doc"], e["page"]): e["final_label"]
           for e in json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))["pages"]}
    rj = json.load(open("results/_fair_total_judging_v2.json"))
    return key, rj


def main():
    key, rj = load()
    # accumulators
    num = lambda: defaultdict(float)
    cnum = defaultdict(num); cden = defaultdict(num)        # cat -> vend -> weighted recall / weight
    crn = defaultdict(num); ccnt = defaultdict(lambda: defaultdict(int))  # cat -> vend -> raw recall sum / count
    cuns = defaultdict(lambda: defaultdict(list))          # cat -> vend -> unsupported list
    cdnum = defaultdict(num); cdden = defaultdict(num)      # (cat,doc) -> vend -> weighted/weight
    rows = []  # for divergence

    for r in rj:
        if r.get("error"): continue
        cat = key.get((r["doc"], r["page"]), "?"); w = r.get("weight", 1)
        recs = {}
        for vd, s in r.get("scores", {}).items():
            ir = s.get("info_recall")
            if ir is None: continue
            recs[vd] = ir
            cnum[cat][vd] += ir*w; cden[cat][vd] += w
            crn[cat][vd] += ir; ccnt[cat][vd] += 1
            if s.get("unsupported") is not None: cuns[cat][vd].append(s["unsupported"])
            cdnum[(cat, r["doc"])][vd] += ir*w; cdden[(cat, r["doc"])][vd] += w
        clean_recs = [recs[v] for v in CLEAN if v in recs]
        if len(clean_recs) >= 2:
            rows.append((cat, r["doc"], r["page"], w, max(clean_recs)-min(clean_recs), recs))

    def ft(cat, vd): return cnum[cat][vd]/cden[cat][vd] if cden[cat][vd] else None
    def mean(cat, vd): return crn[cat][vd]/ccnt[cat][vd] if ccnt[cat][vd] else None
    def uns(cat, vd):
        l = cuns[cat][vd]; return sum(l)/len(l) if l else None
    def p(x): return f"{x:.0f}%" if x is not None else "–"

    L = []; w = L.append
    w("# Per-category audit — which vendor is good at what (v2 corrected GT)")
    w("")
    w("Fair total (weighted) per page category, with sample size, mean recall, and fidelity. "
      "gpt-5 rows (◆) are upper bounds (built the GT). **Image/Photo n is tiny — see the warning.**")
    w("")
    # sample sizes
    ncat = {c: max(ccnt[c][v] for v in ALL) for c in CATS}
    w("**Pages per category (n):** " + ", ".join(f"{c} {ncat[c]}" for c in CATS))
    w("")
    for cat in CATS:
        n = ncat[cat]
        warn = "  ⚠️ **n too small to draw vendor conclusions**" if n < 10 else ""
        w(f"## {cat}  (n={n}){warn}")
        w("")
        w("| Vendor | Fair total | Mean recall | Unsupported |")
        w("|---|---:|---:|---:|")
        ranked = sorted(ALL, key=lambda v: -(ft(cat, v) or -1))
        for vd in ranked:
            w(f"| {VEND_LABEL[vd]} | {p(ft(cat,vd))} | {p(mean(cat,vd))} | {p(uns(cat,vd))} |")
        # winner gap among clean
        cr = sorted([(ft(cat, v), v) for v in CLEAN if ft(cat, v) is not None], reverse=True)
        if len(cr) >= 2:
            gap = cr[0][0]-cr[1][0]
            w("")
            w(f"**Clean winner:** {VEND_LABEL[cr[0][1]]} ({p(cr[0][0])}), "
              f"+{gap:.0f}pp over {VEND_LABEL[cr[1][1]]}.")
        w("")
        # doc cross-tab
        docs = sorted({d for (c, d) in cdnum if c == cat}, key=lambda d: DOC_SHORT.get(d, d))
        if len(docs) > 1:
            w(f"_By document_ (exposes doc/category confound):")
            w("")
            hdr = "| Vendor | " + " | ".join(DOC_SHORT.get(d, d)+f" (n={int(max(cdden[(cat,d)][v] for v in ALL) and sum(1 for r in rj if key.get((r['doc'],r['page']))==cat and r['doc']==d))})" for d in docs) + " |"
            w(hdr); w("|---|" + "---:|"*len(docs))
            for vd in ranked:
                cells = []
                for d in docs:
                    val = cdnum[(cat, d)][vd]/cdden[(cat, d)][vd] if cdden[(cat, d)][vd] else None
                    cells.append(p(val))
                w(f"| {VEND_LABEL[vd]} | " + " | ".join(cells) + " |")
            w("")

    # divergence worklist
    w("## Highest-divergence pages per category (hand-audit targets)")
    w("")
    w("Pages where clean vendors disagree most (max−min recall). These are where the category "
      "score is being decided — read GT vs vendor here to confirm the gap is real, not a judge artifact.")
    w("")
    by_cat = defaultdict(list)
    for cat, doc, page, wt, spread, recs in rows:
        by_cat[cat].append((spread, wt, doc, page, recs))
    worklist = {}
    for cat in CATS:
        top = sorted(by_cat[cat], reverse=True)[:6]
        worklist[cat] = [(d, pg) for _, _, d, pg, _ in top]
        if not top: continue
        w(f"### {cat}")
        for spread, wt, doc, page, recs in top:
            order = sorted(CLEAN, key=lambda v: -(recs.get(v, -1)))
            rec_s = " ".join(f"{v.split('_')[0][:4]}:{recs.get(v,'-')}" for v in order)
            w(f"- {DOC_SHORT.get(doc,doc)} p{page} (w{wt}, spread {spread:.0f}): {rec_s}")
        w("")
    open("results/CATEGORY_AUDIT.md", "w").write("\n".join(L)+"\n")
    json.dump(worklist, open("results/_category_worklist.json", "w"), indent=1)
    print("wrote results/CATEGORY_AUDIT.md and results/_category_worklist.json")
    print("\n".join(L))


if __name__ == "__main__":
    main()
