#!/usr/bin/env python3
"""DETERMINISTIC audit of the element-level eval, for publication hardening.

Re-derives every published number straight from the raw judge JSON (not element_report.py),
and stress-tests the methodology choices a hostile vendor would attack:
  1. VEND_CAP=6000 truncation — per vendor, how many pages are cut, and does truncation
     land on chart/diagram figure descriptions (which build_vendor_md appends LAST)?
  2. GT_CAP=9000 (Stage A) truncation of the GT decomposition input.
  3. Stage-B JSON completeness — did the judge actually return a score for every GT element
     on every page (max_output_tokens=8000 could silently drop trailing elements)?
  4. Independent re-derivation of the per-type recall table; diff vs the published ELEMENT_AUDIT.
  5. Salience-weight sensitivity (weighted vs unweighted ranking).
  6. coverage-threshold sensitivity (>=50 vs >=70).
  7. Per-type bootstrap 95% CIs on each clean winner's lead.
  8. Empty / degenerate vendor pages.
"""
import json, math, statistics
from collections import defaultdict

VENDORS = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
           "landingai", "llamaparse", "pymupdf", "tesseract"]
CLEAN = ["gemini_flash", "gemini_flash_lite", "landingai", "pymupdf", "llamaparse", "tesseract"]
TYPE_ORDER = ["data_table", "chart", "diagram", "kpi_callout", "narrative_text",
              "title_heading", "footnote_source"]
VEND_CAP = 6000
GT_CAP = 9000

import sys, os
sys.path.insert(0, "scripts")
from build_vendor_md import load_pages

def hr(t): print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)

# ---- load ----
gt_rows = json.load(open("results/_gt_elements.json"))
gt_md = {(r["doc"], r["page"]): r.get("md", "") for r in json.load(open("results/_gt_markdown.json"))}
elems = {}            # (doc,page,id) -> (type, salience)
elems_per_page = defaultdict(list)
for r in gt_rows:
    for e in r["elements"]:
        elems[(r["doc"], r["page"], e["id"])] = (e["type"], e.get("salience", 3))
        elems_per_page[(r["doc"], r["page"])].append(e["id"])
judg = json.load(open("results/_element_judging.json"))
vendor_md = {vd: load_pages(vd) for vd in VENDORS}

# ---- 1. VEND_CAP truncation ----
hr("1. VEND_CAP=6000 truncation incidence (Stage B judge input)")
print(f"{'vendor':<20}{'pages>6k':>9}{'%pages':>8}{'maxlen':>9}{'chars_cut_total':>16}")
trunc_pages = defaultdict(set)
for vd in VENDORS:
    lens = [len(v) for v in vendor_md[vd].values()]
    over = [L for L in lens if L > VEND_CAP]
    cut = sum(L - VEND_CAP for L in over)
    for k, v in vendor_md[vd].items():
        if len(v) > VEND_CAP:
            trunc_pages[vd].add(k)
    print(f"{vd:<20}{len(over):>9}{100*len(over)/len(lens):>7.1f}%{(max(lens) if lens else 0):>9}{cut:>16,}")

# Does truncation land on chart/diagram pages specifically? For each truncated vendor-page,
# count GT chart/diagram elements present on it (those are the ones at risk).
hr("1b. Truncated vendor-pages that CONTAIN chart/diagram elements (recall-at-risk)")
print(f"{'vendor':<20}{'trunc pages':>12}{'w/ chart/diag GT':>18}{'chart+diag elems on them':>26}")
for vd in VENDORS:
    tp = trunc_pages[vd]
    with_fig = 0; fig_elems = 0
    for k in tp:
        ce = [eid for eid in elems_per_page[k] if elems[(k[0], k[1], eid)][0] in ("chart", "diagram")]
        if ce:
            with_fig += 1; fig_elems += len(ce)
    print(f"{vd:<20}{len(tp):>12}{with_fig:>18}{fig_elems:>26}")

# ---- 2. GT_CAP truncation ----
hr("2. GT_CAP=9000 truncation in Stage A (decomposition input)")
over = [(k, len(v)) for k, v in gt_md.items() if len(v) > GT_CAP]
print(f"GT pages with md > 9000 chars: {len(over)} / {len(gt_md)}")
for k, L in sorted(over, key=lambda x: -x[1])[:10]:
    print(f"  {k[0][:28]:<30} p{k[1]:<4} {L:>7} chars  ({L-GT_CAP} cut, {len(elems_per_page[k])} elems found)")

# ---- 3. Stage B completeness ----
hr("3. Stage-B JSON completeness (did judge score every GT element?)")
missing_pages = 0; missing_elems = 0; err_pages = 0
for pg in judg:
    if pg.get("error"):
        err_pages += 1; continue
    scored = {s["id"] for s in pg.get("scores", [])}
    want = set(elems_per_page[(pg["doc"], pg["page"])])
    miss = want - scored
    if miss:
        missing_pages += 1; missing_elems += len(miss)
print(f"error pages: {err_pages}   pages with >=1 unscored GT element: {missing_pages}   "
      f"total unscored elements: {missing_elems} / {len(elems)}")
# also: did any vendor letter get dropped within a scored element?
vd_missing = defaultdict(int)
for pg in judg:
    for s in pg.get("scores", []):
        for vd in VENDORS:
            if vd not in s.get("vendors", {}):
                vd_missing[vd] += 1
print("per-vendor element-scores missing (vendor key absent in a scored element):",
      dict(vd_missing) or "none")

# ---- 4. independent re-derivation of recall table ----
hr("4. Independent re-derivation: salience-weighted recall by type (raw JSON)")
def aggregate(weight=True, cov_thresh=50):
    R = defaultdict(lambda: defaultdict(float)); S = defaultdict(lambda: defaultdict(float))
    CAP = defaultdict(lambda: defaultdict(int)); N = defaultdict(lambda: defaultdict(int))
    raw = defaultdict(lambda: defaultdict(list))  # for CI
    for pg in judg:
        if pg.get("error"): continue
        for s in pg.get("scores", []):
            meta = elems.get((pg["doc"], pg["page"], s["id"]))
            if not meta: continue
            typ, sal = meta
            w = sal if weight else 1
            for vd, sc in s["vendors"].items():
                rec = sc.get("recall")
                if rec is None: continue
                R[typ][vd] += rec * w; S[typ][vd] += w
                if rec >= cov_thresh: CAP[typ][vd] += 1
                N[typ][vd] += 1
                raw[typ][vd].append((rec, sal))
    return R, S, CAP, N, raw
R, S, CAP, N, raw = aggregate()
hdr = f"{'type':<16}" + "".join(f"{v.split('_')[0][:5]:>7}" for v in VENDORS)
print(hdr)
for t in TYPE_ORDER:
    line = f"{t:<16}"
    for v in VENDORS:
        val = R[t][v] / S[t][v] if S[t][v] else float('nan')
        line += f"{val:>7.1f}"
    print(line)
print("\n(compare these to ELEMENT_AUDIT.md; any mismatch = report-script bug)")

# ---- 5. salience sensitivity ----
hr("5. Salience-weight sensitivity — clean winner per type (weighted vs UNWEIGHTED)")
Ru, Su, _, _, _ = aggregate(weight=False)
print(f"{'type':<16}{'weighted winner':<26}{'unweighted winner':<26}{'flip?':>6}")
for t in TYPE_ORDER:
    wsort = sorted([(R[t][v]/S[t][v], v) for v in CLEAN if S[t][v]], reverse=True)
    usort = sorted([(Ru[t][v]/Su[t][v], v) for v in CLEAN if Su[t][v]], reverse=True)
    flip = "FLIP" if wsort[0][1] != usort[0][1] else ""
    print(f"{t:<16}{wsort[0][1]+f' ({wsort[0][0]:.0f})':<26}{usort[0][1]+f' ({usort[0][0]:.0f})':<26}{flip:>6}")

# ---- 6. coverage threshold sensitivity ----
hr("6. Coverage-threshold sensitivity (recall>=50 vs >=70) — clean winner per type")
_, _, CAP50, N50, _ = aggregate(cov_thresh=50)
_, _, CAP70, N70, _ = aggregate(cov_thresh=70)
for t in TYPE_ORDER:
    s50 = sorted([(100*CAP50[t][v]/N50[t][v], v) for v in CLEAN if N50[t][v]], reverse=True)
    s70 = sorted([(100*CAP70[t][v]/N70[t][v], v) for v in CLEAN if N70[t][v]], reverse=True)
    print(f"{t:<16} cov50 winner {s50[0][1]:<18}({s50[0][0]:.0f})   cov70 winner {s70[0][1]:<18}({s70[0][0]:.0f})")

# ---- 7. bootstrap CI on clean winner's lead ----
hr("7. Bootstrap 95% CI on the clean winner's recall lead over runner-up (salience-weighted)")
def wmean(pairs):  # pairs of (rec, sal)
    num = sum(r*s for r, s in pairs); den = sum(s for _, s in pairs)
    return num/den if den else float('nan')
import random
rng = random.Random(42)
for t in TYPE_ORDER:
    means = sorted([(wmean(raw[t][v]), v) for v in CLEAN if raw[t][v]], reverse=True)
    w, ru = means[0][1], means[1][1]
    # paired bootstrap over elements where both have a score: use index alignment via page-element list
    # rebuild aligned per-element pairs
    aligned = []
    for pg in judg:
        if pg.get("error"): continue
        for s in pg.get("scores", []):
            m = elems.get((pg["doc"], pg["page"], s["id"]))
            if not m or m[0] != t: continue
            vw = s["vendors"].get(w); vr = s["vendors"].get(ru)
            if vw and vr and vw.get("recall") is not None and vr.get("recall") is not None:
                aligned.append((vw["recall"], vr["recall"], m[1]))
    diffs = []
    n = len(aligned)
    for _ in range(2000):
        samp = [aligned[rng.randrange(n)] for _ in range(n)]
        num_w = sum(a*s for a, _, s in samp); num_r = sum(b*s for _, b, s in samp)
        den = sum(s for _, _, s in samp)
        diffs.append((num_w-num_r)/den)
    diffs.sort()
    lo, hi = diffs[int(0.025*len(diffs))], diffs[int(0.975*len(diffs))]
    pt = means[0][0]-means[1][0]
    sig = "" if lo > 0 else "  <-- CI crosses 0 (TIE)"
    print(f"{t:<16} {w} > {ru}: +{pt:.1f}  95%CI[{lo:+.1f},{hi:+.1f}] n={n}{sig}")

# ---- 8. empty / degenerate vendor pages ----
hr("8. Empty / degenerate vendor pages (page_md blank => recall 0 on all its elements)")
for vd in VENDORS:
    empties = [k for k, v in vendor_md[vd].items() if not (v and v.strip())]
    print(f"{vd:<20} empty pages: {len(empties)}  {empties[:6]}")
