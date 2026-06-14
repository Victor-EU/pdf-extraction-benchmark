#!/usr/bin/env python3
"""Compare per-vendor FAIR TOTAL under v1 GT vs corrected v2 GT.

Loads two fair-total judging files (v1 = results/_fair_total_judging.json, v2 =
results/_fair_total_judging_v2.json), recomputes the density-weighted fair total per vendor
and per category, and reports the deltas + ranking change. The point: show whether correcting
the GT's chart-data errors moves any vendor's score or the overall ranking — i.e. whether the
twin-bias the audit found is material to the conclusions.

Output: results/FAIR_TOTAL_V1_V2.md
"""
import json, os
from collections import defaultdict

VEND_LABEL = {
    "gpt5_image": "gpt-5 (image) ◆", "gpt5_file": "gpt-5 (file) ◆",
    "gemini_flash": "Gemini 3.5 Flash", "gemini_flash_lite": "Gemini 3.1 Flash-Lite",
    "landingai": "Landing AI", "llamaparse": "LlamaParse",
    "pymupdf": "PyMuPDF", "tesseract": "Tesseract",
}
ORDER = ["gemini_flash", "gemini_flash_lite", "landingai", "pymupdf", "llamaparse",
         "tesseract", "gpt5_image", "gpt5_file"]
CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]


def fair_totals(path, key):
    fj = json.load(open(path))
    num = defaultdict(float); den = defaultdict(float)
    cnum = defaultdict(lambda: defaultdict(float)); cden = defaultdict(lambda: defaultdict(float))
    unsup = defaultdict(list)
    for r in fj:
        if r.get("error"): continue
        w = r.get("weight", 1); cat = key.get((r["doc"], r["page"]), "?")
        for vd, s in r.get("scores", {}).items():
            ir = s.get("info_recall")
            if ir is None: continue
            num[vd] += ir*w; den[vd] += w
            cnum[vd][cat] += ir*w; cden[vd][cat] += w
            if s.get("unsupported") is not None: unsup[vd].append(s["unsupported"])
    ft = {vd: num[vd]/den[vd]/100 for vd in num if den[vd]}
    catft = {vd: {c: (cnum[vd][c]/cden[vd][c]/100 if cden[vd][c] else None) for c in CATS} for vd in num}
    un = {vd: (sum(unsup[vd])/len(unsup[vd])/100 if unsup[vd] else None) for vd in num}
    return ft, catft, un


def main():
    key = {(e["doc"], e["page"]): e["final_label"]
           for e in json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))["pages"]}
    v1, c1, u1 = fair_totals("results/_fair_total_judging_v1.json", key)
    v2p = "results/_fair_total_judging_v2.json"
    if not os.path.exists(v2p):
        print("v2 judging not found yet:", v2p); return
    v2, c2, u2 = fair_totals(v2p, key)

    def pct(x): return f"{100*x:.1f}%" if x is not None else "–"
    def dlt(a, b):
        if a is None or b is None: return "–"
        d = 100*(b-a); return f"{d:+.1f}"

    rank1 = sorted([v for v in ORDER if v not in ("gpt5_image","gpt5_file")], key=lambda v:-v1.get(v,0))
    rank2 = sorted([v for v in ORDER if v not in ("gpt5_image","gpt5_file")], key=lambda v:-v2.get(v,0))

    L=[]; w=L.append
    w("# Fair total — v1 GT vs corrected v2 GT")
    w("")
    w("Same vendor extractions, same blind gpt-5 judge, **only the ground-truth reference changed** "
      "(v2 = figure pages rebuilt with the authoritative text layer + 2400px render). This isolates "
      "the effect of correcting the GT's chart-data errors on the headline ranking.")
    w("")
    w("| Vendor | v1 fair total | v2 fair total | Δ (pp) | v1 unsup | v2 unsup |")
    w("|---|---:|---:|---:|---:|---:|")
    for vd in ORDER:
        w(f"| {VEND_LABEL[vd]} | {pct(v1.get(vd))} | {pct(v2.get(vd))} | {dlt(v1.get(vd),v2.get(vd))} | {pct(u1.get(vd))} | {pct(u2.get(vd))} |")
    w("")
    w(f"**Ranking (clean vendors) v1:** {' > '.join(VEND_LABEL[v].replace(' ◆','') for v in rank1)}")
    w("")
    w(f"**Ranking (clean vendors) v2:** {' > '.join(VEND_LABEL[v].replace(' ◆','') for v in rank2)}")
    w("")
    w(f"**Ranking changed:** {'YES' if rank1!=rank2 else 'NO — identical order'}")
    w("")
    w("## Chart/Diagram + Mixed fair total (where the GT was corrected)")
    w("")
    w("| Vendor | Chart v1 | Chart v2 | Δ | Mixed v1 | Mixed v2 | Δ |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    for vd in ORDER:
        w(f"| {VEND_LABEL[vd]} | {pct(c1[vd]['Chart/Diagram'])} | {pct(c2[vd]['Chart/Diagram'])} | "
          f"{dlt(c1[vd]['Chart/Diagram'],c2[vd]['Chart/Diagram'])} | "
          f"{pct(c1[vd]['Mixed'])} | {pct(c2[vd]['Mixed'])} | {dlt(c1[vd]['Mixed'],c2[vd]['Mixed'])} |")
    w("")
    open("results/FAIR_TOTAL_V1_V2.md","w").write("\n".join(L)+"\n")
    print("wrote results/FAIR_TOTAL_V1_V2.md\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
