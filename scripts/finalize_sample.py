#!/usr/bin/env python3
"""Apply deep-think tie-break decisions -> final sample ground-truth answer key.

Vision is the anchor; final_label = vision label EXCEPT where the deep-think
re-examination revised it (recorded in REVISIONS). Each page also gets a
confidence and, for tie-broken pages, a note explaining the resolution.
"""
import json
from collections import Counter

# Pages re-examined in the deep-think tie-break. Key (doc_prefix, page).
# value = (final_label, note). doc matched by startswith for brevity.
TIEBREAK = {
    ("20190308", 1):   ("Cover/Divider", "PHOTO-DIVIDER RULE: title slide w/ decorative deer photo; det+la see big image->Image/Photo but it is functionally a cover. Vision holds."),
    ("20190308", 108): ("Mixed",         "3 product rows: small thumbnail photos + mini price-tables + logos; no type dominates. la's Image/Photo over-weights small thumbnails. Vision holds."),
    ("20190308", 110): ("Mixed",         "2 product rows photos+tables+logos, sparse; no dominant type. Vision holds."),
    ("IAR", 1):        ("Cover/Divider", "PHOTO-DIVIDER RULE: title cover + full-bleed cyclist photo; functionally a cover. Vision holds."),
    ("IAR", 14):       ("Mixed",         "Prose columns + Venn diagram + comparison table = three distinct types, none dominant. Vision holds."),
    ("IAR", 41):       ("Mixed",         "Two bar charts (left) + three testimonial text cards (right), ~half/half real content. Vision holds (not chart-dominant)."),
    ("IAR", 75):       ("Mixed",         "Numbered text list (6 pts, left) + bar charts + NPS (right). Text is substantial content, not annotation. Vision holds."),
    ("IAR", 82):       ("Cover/Divider", "PHOTO-DIVIDER RULE: section divider 'Non-Financial Information' + full-bleed beach photo. Vision holds."),
    ("IAR", 160):      ("Mixed",         "Intro prose + employee photo + circular HR cycle diagram = three types. Vision holds."),
    ("IAR", 228):      ("Text",          "EY assurance letter, full-page prose. det(Image)+la(Cover) are CORRELATED logo+whitespace misfires, not real corroboration. Vision holds."),
    ("IAR", 237):      ("Text",          "EY audit report continued: substantive prose + signature, whitespace below. det+la->Cover is a shared density-heuristic failure. Vision holds."),
    ("IAR", 310):      ("Cover/Divider", "PHOTO-DIVIDER RULE: back cover, logo + full-bleed aerial photo. Vision holds."),
    ("SOTER", 1):      ("Cover/Divider", "PHOTO-DIVIDER RULE: title slide + decorative network illustration. Vision holds."),
    ("SOTER", 3):      ("Text",          "Contact-details slide: 3 full contact blocks = substantive text content, not a section break. la's Cover over-weights whitespace. Vision holds."),
    ("SOTER", 11):     ("Table",         "Full-page comparison matrix (10 verticals x attributes); logos are cell content in one column. la's Image/Photo over-weights logos. Vision holds."),
    ("SOTER", 34):     ("Mixed",         "Large site photo (~half) + three case-study prose boxes (~40%); neither dominates. la's Image/Photo over-weights largest element. Vision holds (borderline)."),
    ("SOTER", 42):     ("Cover/Divider", "PHOTO-DIVIDER RULE: section divider 'III. Market...' + line illustration. Vision holds."),
    ("SOTER", 46):     ("Chart/Diagram", "M2M ecosystem/network diagram dominates. la's Image/Photo treats the diagram as a picture; det's Text wrong. Vision holds."),
    ("SOTER", 62):     ("Chart/Diagram", "REVISED from Mixed: page is organized AS a chevron process-flow diagram + 2 pie charts; bullet text is stage annotation. Both cross-checks concur (semantic, not correlated error). Deep-think changed the call."),
    ("SOTER", 91):     ("Cover/Divider", "PHOTO-DIVIDER RULE: section divider 'VII. Employees...' + line illustration. Vision holds."),
    ("SOTER", 133):    ("Cover/Divider", "PHOTO-DIVIDER RULE: back cover, AddSecure branded image + address blocks. Vision holds."),
}

# Pages where the FINAL label differs from the original vision label (audit trail)
REVISED_FROM_VISION = {("SOTER", 62): "Mixed"}


def tb_lookup(doc, page):
    for (pref, pg), val in TIEBREAK.items():
        if page == pg and doc.startswith(pref):
            return val
    return None


def conf_for(row, was_tiebreak):
    if was_tiebreak:
        # tie-break resolved; confidence reflects residual ambiguity
        hard = {("20190308", 108), ("SOTER", 34), ("SOTER", 62), ("IAR", 41)}
        for (pref, pg) in hard:
            if row["page"] == pg and row["doc"].startswith(pref):
                return "med-low"
        return "med"
    return row["confidence"]  # high / med-high from agreement pattern


def main():
    rows = json.load(open("ground_truth/reconcile/reconciled.json"))
    final = []
    for r in rows:
        tb = tb_lookup(r["doc"], r["page"])
        was_tb = tb is not None
        if was_tb:
            label, note = tb
        else:
            label, note = r["vision"], None
        final.append(dict(
            doc=r["doc"], page=r["page"],
            final_label=label,
            confidence=conf_for(r, was_tb),
            sources=dict(deterministic=r["det"], vision=r["vision"], landing_ai=r["la"]),
            agreement_pattern=r["pattern"],
            tiebreak=was_tb,
            tiebreak_note=note,
            vision_rationale=r["rationale"],
        ))
    json.dump(dict(n=len(final), note="Sample (60-page) ground-truth answer key. final_label is authoritative.", pages=final),
              open("ground_truth/reconcile/final_ground_truth_sample.json", "w"), indent=2)

    # Report: each source's standalone match-rate vs FINAL truth (previews their accuracy)
    def match(src):
        return sum(1 for r in final if r["sources"][src] == r["final_label"])
    n = len(final)
    print(f"=== FINAL sample ground truth: {n} pages (100% tagged) ===\n")
    print("Each source's agreement with FINAL truth (preview of standalone accuracy):")
    for src in ("vision", "landing_ai", "deterministic"):
        m = match(src)
        print(f"  {src:<14} {m}/{n} = {100*m/n:.0f}%")
    print(f"\nFinal label distribution:")
    for cat, c in Counter(r["final_label"] for r in final).most_common():
        print(f"  {cat:<14} {c:>3}  ({100*c/n:.0f}%)")
    print(f"\nConfidence distribution:")
    for cf, c in Counter(r["confidence"] for r in final).most_common():
        print(f"  {cf:<10} {c}")
    ntb = sum(1 for r in final if r["tiebreak"])
    nrev = sum(1 for r in final if r["tiebreak"] and r["sources"]["vision"] != r["final_label"])
    print(f"\nTie-broken pages: {ntb}  |  vision call revised by deep-think: {nrev}")
    print("Wrote ground_truth/reconcile/final_ground_truth_sample.json")


if __name__ == "__main__":
    main()
