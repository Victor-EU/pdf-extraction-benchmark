#!/usr/bin/env python3
"""Hand-audit one GT element: show its key_facts, the per-vendor recall/wrong the judge gave it,
and the relevant vendors' full page markdown — so a human can confirm the score is fair.
Usage: python3 scripts/dump_element.py <doc_substr> <page> <elem_id> [vend1 vend2 ...]
"""
import json, sys
sys.path.insert(0, "scripts")
from build_vendor_md import load_pages

doc_sub, page, eid = sys.argv[1], int(sys.argv[2]), sys.argv[3]
vends = sys.argv[4:] or ["pymupdf", "landingai", "gemini_flash", "tesseract", "llamaparse"]

els = json.load(open("results/_gt_elements.json"))
rec = next(r for r in els if doc_sub.lower() in r["doc"].lower() and r["page"] == page)
doc = rec["doc"]
el = next(e for e in rec["elements"] if e["id"] == eid)
print(f"### {doc} p{page} [{eid}]  type={el['type']} salience={el['salience']}")
print(f"LABEL: {el['label']}")
print(f"KEY_FACTS: {el['key_facts']}\n")

judg = json.load(open("results/_element_judging.json"))
pg = next(r for r in judg if r["doc"] == doc and r["page"] == page)
s = next((x for x in pg["scores"] if x["id"] == eid), None)
if s:
    print("JUDGE recall/wrong per vendor:")
    for vd in ["gemini_flash", "gemini_flash_lite", "landingai", "pymupdf", "llamaparse",
               "tesseract", "gpt5_image", "gpt5_file"]:
        if vd in s["vendors"]:
            print(f"  {vd:18s} recall={s['vendors'][vd]['recall']:3d} wrong={s['vendors'][vd]['wrong']:3d}")
print()
for vd in vends:
    md = load_pages(vd).get((doc, page), "") or "(empty)"
    cap = md if len(md) < 2500 else md[:2500] + f"\n…[+{len(md)-2500}]"
    print(f"\n{'='*60}\n## {vd.upper()} full page text\n{'='*60}\n{cap}")
