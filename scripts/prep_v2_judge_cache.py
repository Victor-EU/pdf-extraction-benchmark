#!/usr/bin/env python3
"""Pre-populate the v2 fair-total judge cache with v1 results for UNCHANGED pages.

For every page NOT rebuilt in v2 (rebuilt==False in _gt_markdown_v2.json), the judge input is
byte-identical under v1 and v2 (same GT page md, same vendor md), so the v1 judgment applies
exactly — reuse it. score_fair_total.py will then skip those (cache hit) and only call gpt-5 on
the rebuilt figure pages. Saves ~55% of the re-judge cost and removes re-roll noise on unchanged pages.
"""
import json, os, shutil

V1_CACHE = "ground_truth/fair_total_judge"
V2_CACHE = os.environ.get("FT_CACHE", "ground_truth/fair_total_judge_v2")

def main():
    v2 = json.load(open("results/_gt_markdown_v2.json"))
    os.makedirs(V2_CACHE, exist_ok=True)
    copied = rebuilt = missing = 0
    for r in v2:
        doc, page = r["doc"], r["page"]
        fn = f"{doc}__p{page:04d}.json"
        if r.get("rebuilt"):
            rebuilt += 1
            # ensure no stale v1 judgment sits in the v2 cache for a rebuilt page
            dst = os.path.join(V2_CACHE, fn)
            if os.path.exists(dst): os.remove(dst)
            continue
        src = os.path.join(V1_CACHE, fn); dst = os.path.join(V2_CACHE, fn)
        if os.path.exists(src):
            shutil.copyfile(src, dst); copied += 1
        else:
            missing += 1
    print(f"v2 judge cache prepped at {V2_CACHE}: copied {copied} unchanged, "
          f"{rebuilt} rebuilt pages left to judge, {missing} v1-cache misses")

if __name__ == "__main__":
    main()
