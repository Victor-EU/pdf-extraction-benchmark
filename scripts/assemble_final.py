#!/usr/bin/env python3
"""Assemble the final 599-page answer key from agreements + tie-break results."""
import json, glob
from collections import Counter, defaultdict

VALID = {"Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"}
CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]

recon = {(r["doc"], r["page"]): r for r in json.load(open("ground_truth/reconcile/full_reconciled.json"))}

tb = {}
for f in sorted(glob.glob("ground_truth/reconcile/tiebreak_results/tb_*.json")):
    for r in json.load(open(f)):
        tb[(r["doc"], r["page"])] = r

final = []
problems = []
review = []  # still_uncertain or overrode-both
for key in sorted(recon.keys()):
    doc, page = key
    r = recon[key]
    if r["agree"]:
        final_label = r["final"]
        entry = dict(doc=doc, page=page, final_label=final_label,
                     resolution="agreement", confidence="high",
                     vision=r["vision"], landing_ai=r["landing_ai"])
    else:
        t = tb.get(key)
        if not t:
            problems.append(("missing_tiebreak", key)); continue
        final_label = t["final_label"]
        entry = dict(doc=doc, page=page, final_label=final_label,
                     resolution="tiebreak", winner=t.get("winner"),
                     confidence=t.get("confidence"),
                     vision=r["vision"], landing_ai=r["landing_ai"],
                     reasoning=t.get("reasoning"),
                     still_uncertain=bool(t.get("still_uncertain")))
        if t.get("still_uncertain") or t.get("winner") == "other":
            review.append(dict(doc=doc, page=page,
                               png=f"{doc}__p{page:04d}.png",
                               vision=r["vision"], landing_ai=r["landing_ai"],
                               adjudicator=final_label, winner=t.get("winner"),
                               still_uncertain=bool(t.get("still_uncertain")),
                               reasoning=t.get("reasoning")))
    if final_label not in VALID:
        problems.append(("bad_label", key, final_label))
    final.append(entry)

json.dump(dict(n=len(final), pages=final),
          open("ground_truth/reconcile/final_answer_key.json", "w"), indent=2)
json.dump(review, open("ground_truth/reconcile/needs_my_review.json", "w"), indent=2)

n = len(final)
print(f"=== FINAL ANSWER KEY: {n}/599 pages ===")
print(f"problems: {problems if problems else 'none'}")
nag = sum(1 for e in final if e["resolution"] == "agreement")
ntb = n - nag
print(f"  resolved by agreement : {nag} ({100*nag/n:.0f}%)")
print(f"  resolved by tie-break : {ntb} ({100*ntb/n:.0f}%)")

tbe = [e for e in final if e["resolution"] == "tiebreak"]
print(f"\nTie-break winners:")
for w, c in Counter(e.get("winner") for e in tbe).most_common():
    print(f"  {str(w):<12} {c}")
print(f"\nNeeds MY review (still_uncertain or overrode-both): {len(review)}")
for r in review:
    flag = "UNCERTAIN" if r["still_uncertain"] else "OVERRODE-BOTH"
    print(f"  [{flag}] {r['doc'][:30]:<30} p{r['page']:<4} vis={r['vision']:<13} la={r['landing_ai']:<13} -> {r['adjudicator']}")

print(f"\nFINAL category distribution (599):")
for cat in CATS:
    c = sum(1 for e in final if e["final_label"] == cat)
    print(f"  {cat:<14} {c:>3}  ({100*c/n:.0f}%)")
print("\nWrote final_answer_key.json + needs_my_review.json")
