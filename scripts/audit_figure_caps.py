#!/usr/bin/env python3
"""Measure every truncation vector in score_figures.vendor_blob() on the 265 figure-judge pages,
per vendor: per-figure [:1600], per-table [:1200], figure-count [:8], table-count [:6], whole-blob [:7000].
Mirror of the VEND_CAP audit. Decide if a re-judge at higher caps is warranted, and for whom."""
import json
from collections import defaultdict

VENDORS = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
           "landingai", "llamaparse", "pymupdf", "tesseract"]
FIG_CAP, TAB_CAP, NFIG, NTAB, BLOB = 1600, 1200, 8, 6, 7000

key = {(e["doc"], e["page"]): e["final_label"]
       for e in json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))["pages"]}
targets = {(d, p) for (d, p), c in key.items() if c in ("Chart/Diagram", "Mixed")}
print(f"figure-judge target pages (Chart/Diagram + Mixed): {len(targets)}\n")

vend = {vd: {(r["doc"], r["page"]): r for r in json.load(open(f"results/_extract_{vd}.json"))}
        for vd in VENDORS}

def blob_len_uncapped(rec):
    parts = []
    for f in rec.get("figures", [])[:NFIG]:
        parts.append(f"FIGURE[{f.get('kind')}]: " + str(f.get("content", ""))[:FIG_CAP])
    for t in rec.get("tables", [])[:NTAB]:
        parts.append("TABLE: " + str(t)[:TAB_CAP])
    return len("\n".join(parts))

print(f"{'vendor':<20}{'figs>1600':>10}{'tbls>1200':>10}{'pg>8figs':>9}{'pg>6tbls':>9}{'pg blob>7000':>13}{'maxfig':>8}{'maxblob':>9}")
rows = {}
for vd in VENDORS:
    figs_trunc = tbls_trunc = pg_nfig = pg_ntab = pg_blob = 0
    maxfig = maxblob = 0
    for dp in targets:
        r = vend[vd].get(dp, {})
        figs = r.get("figures", []); tbls = r.get("tables", [])
        for f in figs[:NFIG]:
            c = len(str(f.get("content", "")))
            maxfig = max(maxfig, c)
            if c > FIG_CAP: figs_trunc += 1
        for t in tbls[:NTAB]:
            if len(str(t)) > TAB_CAP: tbls_trunc += 1
        if len(figs) > NFIG: pg_nfig += 1
        if len(tbls) > NTAB: pg_ntab += 1
        bl = blob_len_uncapped(r)
        maxblob = max(maxblob, bl)
        if bl > BLOB: pg_blob += 1
    rows[vd] = (figs_trunc, tbls_trunc, pg_nfig, pg_ntab, pg_blob, maxfig, maxblob)
    print(f"{vd:<20}{figs_trunc:>10}{tbls_trunc:>10}{pg_nfig:>9}{pg_ntab:>9}{pg_blob:>13}{maxfig:>8}{maxblob:>9}")

# union of pages where ANY vendor hits ANY cap -> would need re-judge
affected = set()
for vd in VENDORS:
    for dp in targets:
        r = vend[vd].get(dp, {})
        figs = r.get("figures", []); tbls = r.get("tables", [])
        hit = (any(len(str(f.get("content", ""))) > FIG_CAP for f in figs[:NFIG]) or
               any(len(str(t)) > TAB_CAP for t in tbls[:NTAB]) or
               len(figs) > NFIG or len(tbls) > NTAB or blob_len_uncapped(r) > BLOB)
        if hit: affected.add(dp)
print(f"\nPages where >=1 vendor hits >=1 cap (re-judge candidates): {len(affected)} / {len(targets)}")
# Landing-AI-only affected
la_only = set()
for dp in targets:
    r = vend["landingai"].get(dp, {})
    figs = r.get("figures", []); tbls = r.get("tables", [])
    if (any(len(str(f.get("content", ""))) > FIG_CAP for f in figs[:NFIG]) or
        any(len(str(t)) > TAB_CAP for t in tbls[:NTAB]) or
        len(figs) > NFIG or len(tbls) > NTAB or blob_len_uncapped(r) > BLOB):
        la_only.add(dp)
print(f"Pages where LANDING AI specifically hits a cap: {len(la_only)}")
json.dump([list(x) for x in sorted(affected)], open("results/_rejudge_pages_fig.json", "w"))
