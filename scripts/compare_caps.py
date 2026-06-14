#!/usr/bin/env python3
"""Compare element-level recall by type between the canonical run (VEND_CAP=6000)
and the re-judge with VEND_CAP=16000 (no truncation). Quantifies the truncation artifact."""
import json
from collections import defaultdict

VENDORS = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
           "landingai", "llamaparse", "pymupdf", "tesseract"]
CLEAN = ["gemini_flash", "gemini_flash_lite", "landingai", "pymupdf", "llamaparse", "tesseract"]
TYPE_ORDER = ["data_table", "chart", "diagram", "kpi_callout", "narrative_text",
              "title_heading", "footnote_source"]

elems = {}
for r in json.load(open("results/_gt_elements.json")):
    for e in r["elements"]:
        elems[(r["doc"], r["page"], e["id"])] = (e["type"], e.get("salience", 3))

def agg(path):
    judg = json.load(open(path))
    R = defaultdict(lambda: defaultdict(float)); S = defaultdict(lambda: defaultdict(float))
    for pg in judg:
        if pg.get("error"): continue
        for s in pg.get("scores", []):
            m = elems.get((pg["doc"], pg["page"], s["id"]))
            if not m: continue
            typ, sal = m
            for vd, sc in s["vendors"].items():
                rec = sc.get("recall")
                if rec is None: continue
                R[typ][vd] += rec*sal; S[typ][vd] += sal
    return {t: {v: (R[t][v]/S[t][v] if S[t][v] else None) for v in VENDORS} for t in TYPE_ORDER}

old = agg("results/_element_judging.json")
new = agg("results/_element_judging_cap16k.json")

print(f"{'type':<16}" + "".join(f"{v.split('_')[0][:5]:>13}" for v in VENDORS))
for t in TYPE_ORDER:
    line = f"{t:<16}"
    for v in VENDORS:
        o, n = old[t][v], new[t][v]
        d = n - o
        flag = "*" if abs(d) >= 2 else " "
        line += f"{o:>4.0f}->{n:>3.0f}{d:>+4.0f}{flag}"
    print(line)
print("\n* = shift >=2 points.  Focus row: landingai (the vendor truncated on 145 pages).")
print("\nLanding AI detail (old -> new, delta):")
for t in TYPE_ORDER:
    o, n = old[t]["landingai"], new[t]["landingai"]
    print(f"  {t:<18} {o:>5.1f} -> {n:>5.1f}  ({n-o:+.1f})")
