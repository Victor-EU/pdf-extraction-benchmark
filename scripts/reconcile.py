#!/usr/bin/env python3
"""Reconcile the three ground-truth votes into a provisional answer key.

Sources per page:
  - det     : deterministic PyMuPDF heuristic   (weak prior)
  - vision  : Claude vision label               (ANCHOR / primary, per user)
  - la      : Landing AI ADE reduced label      (independent cross-check)

Rule (user-specified): ground truth = vision + deterministic, cross-checked with
Landing AI; on disagreement, deep-think tie-break. We anchor the provisional
truth on the vision label and assign a confidence + tie-break flag from the
agreement pattern. Pages flagged `needs_tiebreak` get a manual deep-think pass.
"""
import json, sys
from collections import Counter, defaultdict

CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]


def load():
    la = {(r["doc"], r["page"]): r for r in json.load(open("ground_truth/landingai/labels.json"))}
    vis = {(r["doc"], r["page"]): r for r in json.load(open("ground_truth/vision/claude_labels.json"))["labels"]}
    return la, vis


def pattern(det, vision, la):
    if la == "ERROR" or la is None:
        return ("no_la_vision+det" if det == vision else "no_la_disagree")
    s = {det, vision, la}
    if len(s) == 1:
        return "AAA"               # all three agree
    if vision == la and vision != det:
        return "vision+la"          # anchor + cross-check agree (strong)
    if vision == det and vision != la:
        return "vision+det"         # anchor + heuristic agree, cross-check differs
    if det == la and det != vision:
        return "det+la_vs_vision"   # both others gang up against anchor -> tie-break
    return "all_differ"             # 3 distinct -> tie-break


CONF = {
    "AAA": "high",
    "vision+la": "high",
    "vision+det": "med-high",
    "no_la_vision+det": "med",
    "det+la_vs_vision": "low",      # tie-break
    "all_differ": "low",            # tie-break
    "no_la_disagree": "low",        # tie-break
}
TIEBREAK = {"det+la_vs_vision", "all_differ", "no_la_disagree"}


def main():
    la, vis = load()
    rows = []
    for key in sorted(vis.keys()):
        doc, page = key
        v = vis[key]["vision_label"]
        lr = la.get(key, {})
        d = lr.get("det_label")
        l = lr.get("la_label")
        pat = pattern(d, v, l)
        rows.append(dict(doc=doc, page=page, det=d, vision=v, la=l,
                         pattern=pat, provisional=v,
                         confidence=CONF[pat],
                         needs_tiebreak=pat in TIEBREAK,
                         rationale=vis[key]["rationale"]))
    json.dump(rows, open("ground_truth/reconcile/reconciled.json", "w"), indent=2)

    n = len(rows)
    valid_la = [r for r in rows if r["la"] not in (None, "ERROR")]
    print(f"=== Reconciliation: {n} sample pages ===")
    print(f"Landing AI valid responses: {len(valid_la)}/{n}")
    agree3 = sum(1 for r in rows if r["pattern"] == "AAA")
    vis_la = sum(1 for r in valid_la if r["vision"] == r["la"])
    vis_det = sum(1 for r in rows if r["vision"] == r["det"])
    print(f"\nPairwise agreement (vision = anchor):")
    print(f"  vision vs Landing AI : {vis_la}/{len(valid_la)} = {100*vis_la/max(len(valid_la),1):.0f}%")
    print(f"  vision vs determ.    : {vis_det}/{n} = {100*vis_det/n:.0f}%")
    print(f"  all three agree      : {agree3}/{n} = {100*agree3/n:.0f}%")
    print(f"\nAgreement patterns:")
    for p, c in Counter(r["pattern"] for r in rows).most_common():
        print(f"  {p:<22} {c:>3}   (conf {CONF[p]}{', TIE-BREAK' if p in TIEBREAK else ''})")
    tb = [r for r in rows if r["needs_tiebreak"]]
    print(f"\nNeeds deep-think tie-break: {len(tb)} pages")
    for r in tb:
        print(f"  {r['doc'][:34]:<34} p{r['page']:<4} det={r['det']:<13} vis={r['vision']:<13} la={r['la']}")
    print(f"\nProvisional truth distribution (anchored on vision):")
    for cat, c in Counter(r["provisional"] for r in rows).most_common():
        print(f"  {cat:<14} {c}")
    print("\nWrote ground_truth/reconcile/reconciled.json")


if __name__ == "__main__":
    main()
