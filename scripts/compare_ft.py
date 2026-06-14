#!/usr/bin/env python3
"""Compare document-level FAIR TOTAL (and per-category) between the canonical run (VEND_CAP/GT_CAP=6000)
and the no-truncation re-judge (cap=16000), for both judge families. Quantifies the truncation artifact
on the PUBLISHED headline number."""
import json, sys
from collections import defaultdict

VENDORS = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
           "landingai", "llamaparse", "pymupdf", "tesseract"]
key = {(e["doc"], e["page"]): e["final_label"]
       for e in json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))["pages"]}
CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]

def ft(path):
    fj = json.load(open(path))
    num = defaultdict(float); den = defaultdict(float)
    cn = defaultdict(lambda: defaultdict(float)); cd = defaultdict(lambda: defaultdict(float))
    unsup = defaultdict(list)
    for r in fj:
        if r.get("error"): continue
        w = r.get("weight", 1); cat = key.get((r["doc"], r["page"]), "?")
        for vd, s in r.get("scores", {}).items():
            ir = s.get("info_recall")
            if ir is None: continue
            num[vd] += ir*w; den[vd] += w
            cn[vd][cat] += ir*w; cd[vd][cat] += w
            if s.get("unsupported") is not None: unsup[vd].append(s["unsupported"])
    tot = {vd: (num[vd]/den[vd] if den[vd] else None) for vd in VENDORS}
    cat = {vd: {c: (cn[vd][c]/cd[vd][c] if cd[vd][c] else None) for c in CATS} for vd in VENDORS}
    uns = {vd: (sum(unsup[vd])/len(unsup[vd]) if unsup[vd] else None) for vd in VENDORS}
    return tot, cat, uns

def run(label, oldp, newp):
    print(f"\n===== {label}: FAIR TOTAL  (old cap6000 -> new cap16000) =====")
    to, co, uo = ft(oldp); tn, cn, un = ft(newp)
    print(f"{'vendor':<20}{'old':>6}{'new':>6}{'Δ':>6}{'  | unsup old->new':>20}")
    for vd in sorted(VENDORS, key=lambda v: -(tn[v] or 0)):
        d = (tn[vd]-to[vd])
        flag = " *" if abs(d) >= 1.5 else ""
        print(f"{vd:<20}{to[vd]:>6.1f}{tn[vd]:>6.1f}{d:>+6.1f}   {uo[vd]:>5.1f}->{un[vd]:<5.1f}{flag}")
    print(f"\n  Landing AI by category (old -> new):")
    for c in CATS:
        o, n = co["landingai"][c], cn["landingai"][c]
        if o is None: continue
        print(f"    {c:<16} {o:>5.1f} -> {n:>5.1f}  ({n-o:+.1f})")

run("gpt-5 judge", "results/_fair_total_judging.json", "results/_fair_total_judging_cap16k.json")
run("Gemini judge", "results/_fair_total_judging_gemini_v2.json", "results/_fair_total_judging_gemini_cap16k.json")
