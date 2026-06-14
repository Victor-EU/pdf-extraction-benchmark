#!/usr/bin/env python3
"""Two-source reconcile (Claude vision + Landing AI) across all 599 pages.

Agree -> locked (final). Disagree -> emit to disagreements.json for deep-think
tie-break. Vision is the anchor for provisional labels. Prints agreement stats
overall, per category, and per document.
"""
import json
from collections import Counter, defaultdict

CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]


def main():
    vis = {(r["doc"], r["page"]): r
           for r in json.load(open("ground_truth/vision_full/_consolidated.json"))["pages"]}
    la = {(r["doc"], r["page"]): r
          for r in json.load(open("ground_truth/landingai_full/labels.json"))}

    rows, disagree = [], []
    for key in sorted(vis.keys()):
        doc, page = key
        v = vis[key]["label"]
        vc = vis[key].get("confidence", "?")
        vr = vis[key].get("rationale", "")
        lr = la.get(key, {})
        l = lr.get("la_label", "MISSING")
        agree = (v == l)
        row = dict(doc=doc, page=page, png=vis[key].get("png") or lr.get("png"),
                   vision=v, vision_conf=vc, landing_ai=l, agree=agree,
                   final=v if agree else None, vision_rationale=vr,
                   la_detail=lr.get("la_detail"))
        rows.append(row)
        if not agree:
            disagree.append(dict(doc=doc, page=page,
                                 png=f"{doc}__p{page:04d}.png",
                                 vision=v, vision_conf=vc, vision_rationale=vr,
                                 landing_ai=l, la_detail=lr.get("la_detail")))
    json.dump(rows, open("ground_truth/reconcile/full_reconciled.json", "w"), indent=2)
    json.dump(disagree, open("ground_truth/reconcile/disagreements.json", "w"), indent=2)

    n = len(rows)
    nag = sum(1 for r in rows if r["agree"])
    print(f"=== Full reconcile: {n} pages ===")
    print(f"vision == Landing AI : {nag}/{n} = {100*nag/n:.0f}%   (locked)")
    print(f"disagreements        : {n-nag}/{n} = {100*(n-nag)/n:.0f}%   (-> deep-think tie-break)\n")

    print("Agreement by document:")
    bydoc = defaultdict(lambda: [0, 0])
    for r in rows:
        bydoc[r["doc"]][0] += 1
        bydoc[r["doc"]][1] += int(r["agree"])
    for d, (t, a) in bydoc.items():
        print(f"  {d[:38]:<38} {a}/{t} = {100*a/t:.0f}%")

    print("\nAgreement by vision label:")
    bylab = defaultdict(lambda: [0, 0])
    for r in rows:
        bylab[r["vision"]][0] += 1
        bylab[r["vision"]][1] += int(r["agree"])
    for lab in CATS:
        t, a = bylab[lab]
        if t:
            print(f"  {lab:<14} {a}/{t} = {100*a/t:.0f}%")

    print("\nDisagreements by vision_confidence:")
    for c, k in Counter(r["vision_conf"] for r in disagree).most_common():
        print(f"  {c:<6} {k}")

    print("\nMost common disagreement pairs (vision -> landing_ai):")
    for (pair), k in Counter((r["vision"], r["landing_ai"]) for r in disagree).most_common(12):
        print(f"  {pair[0]:<14} -> {pair[1]:<14} {k}")
    print(f"\nWrote full_reconciled.json + disagreements.json ({len(disagree)} to tie-break)")


if __name__ == "__main__":
    main()
