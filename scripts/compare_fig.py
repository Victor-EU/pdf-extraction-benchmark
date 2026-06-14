#!/usr/bin/env python3
"""Compare figure-dimension scores (graph-data fidelity, diagram-structure fidelity) between the
canonical run (caps 1600/1200/8/6/7000) and the no-truncation re-judge. Per vendor + the
Gemini-vs-LandingAI gap that FINAL_REPORT §4 publishes."""
import json
from collections import defaultdict

VENDORS = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
           "landingai", "llamaparse", "pymupdf", "tesseract"]

def agg(path):
    fig = json.load(open(path))
    g = defaultdict(list); d = defaultdict(list)
    for r in fig:
        if r.get("error"): continue
        for vd, s in r.get("scores", {}).items():
            gs, ds = s.get("graph_score"), s.get("diagram_score")
            if gs is not None: g[vd].append(gs)
            if ds is not None: d[vd].append(ds)
    gm = {vd: (sum(g[vd])/len(g[vd]) if g[vd] else None) for vd in VENDORS}
    dm = {vd: (sum(d[vd])/len(d[vd]) if d[vd] else None) for vd in VENDORS}
    ng = {vd: len(g[vd]) for vd in VENDORS}; nd = {vd: len(d[vd]) for vd in VENDORS}
    return gm, dm, ng, nd

go, do, ngo, ndo = agg("results/_figure_judging.json")
gn, dn, ngn, ndn = agg("results/_figure_judging_nocap.json")

print(f"{'vendor':<20}{'graph old->new':>20}{'  Δ':>6}   {'diagram old->new':>20}{'  Δ':>6}")
for vd in VENDORS:
    gd = (gn[vd]-go[vd]) if (gn[vd] is not None and go[vd] is not None) else 0
    dd = (dn[vd]-do[vd]) if (dn[vd] is not None and do[vd] is not None) else 0
    fg = "*" if abs(gd) >= 1.5 else " "; fd = "*" if abs(dd) >= 1.5 else " "
    print(f"{vd:<20}{go[vd]:>9.1f}->{gn[vd]:>7.1f}{gd:>+6.1f}{fg}  {do[vd]:>9.1f}->{dn[vd]:>7.1f}{dd:>+6.1f}{fd}")

print("\nPublished §4 gap (graph-data, diagram-structure), clean leaders:")
print(f"  graph-data:   Gemini Flash {go['gemini_flash']:.0f}->{gn['gemini_flash']:.0f}  "
      f"Landing AI {go['landingai']:.0f}->{gn['landingai']:.0f}  "
      f"gap {go['gemini_flash']-go['landingai']:+.0f} -> {gn['gemini_flash']-gn['landingai']:+.0f}")
print(f"  diagram-struct: Gemini Flash {do['gemini_flash']:.0f}->{dn['gemini_flash']:.0f}  "
      f"Landing AI {do['landingai']:.0f}->{dn['landingai']:.0f}  "
      f"gap {do['gemini_flash']-do['landingai']:+.0f} -> {dn['gemini_flash']-dn['landingai']:+.0f}")
print(f"\n  sample sizes (graph n / diagram n) — should be identical old vs new:")
for vd in VENDORS:
    print(f"    {vd:<18} graph {ngo[vd]}->{ngn[vd]}   diagram {ndo[vd]}->{ndn[vd]}")
