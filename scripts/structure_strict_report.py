#!/usr/bin/env python3
"""Compare structure-strict vs canonical fair-total on the SAME diagram pages.

Paired by (doc,page): the per-vendor mean delta (strict - canonical info_recall) isolates the
rubric change (structure-fidelity vs information-presence), since pages/vendors/shuffle/caps
are identical. A large negative delta for a vendor = the canonical metric was crediting token
presence that does not survive a structure-fidelity bar (i.e. that vendor's score was inflated
by structure loss). Structure-aware vendors should barely move.
"""
import json, sys
sys.path.insert(0, "scripts")
from build_vendor_md import VENDORS

DISP = {"gemini_flash": "Gemini 3.5 Flash", "gemini_flash_lite": "Gemini 3.1 Flash-Lite",
        "llamaparse": "LlamaParse (agentic)", "landingai": "Landing AI", "pymupdf": "PyMuPDF",
        "tesseract": "Tesseract", "gpt5_file": "gpt-5 file ◆", "gpt5_image": "gpt-5 image ◆"}
ORDER = ["gemini_flash", "gpt5_image", "gpt5_file", "landingai", "llamaparse",
         "gemini_flash_lite", "pymupdf", "tesseract"]


def main():
    strict = {(r["doc"], r["page"]): r for r in json.load(open("results/_structure_strict_judging.json"))}
    canon = {(r["doc"], r["page"]): r for r in json.load(open("results/_fair_total_judging.json"))}
    pages = sorted(strict.keys())

    rows = []
    for v in ORDER:
        cs = []; ss = []
        for k in pages:
            c = canon[k]["scores"].get(v); s = strict[k]["scores"].get(v)
            if not c or not s or c.get("info_recall") is None or s.get("info_recall") is None:
                continue
            cs.append(c["info_recall"]); ss.append(s["info_recall"])
        n = len(cs)
        cm = sum(cs) / n; sm = sum(ss) / n
        rows.append((v, cm, sm, sm - cm, n))

    print(f"\nStructure-strict re-judge on {len(pages)} relational-DIAGRAM pages")
    print(f"(paired with canonical fair-total; per-page mean info_recall)\n")
    print(f"{'Vendor':24} {'canonical':>10} {'strict':>8} {'Δ':>7}")
    print("-" * 52)
    for v, cm, sm, d, n in rows:
        print(f"{DISP[v]:24} {cm:10.1f} {sm:8.1f} {d:+7.1f}")
    # rank-correlation sanity: who moved most
    worst = sorted(rows, key=lambda r: r[3])[:3]
    print("\nLargest drops (most structure-inflated):",
          ", ".join(f"{DISP[v]} {d:+.0f}" for v, cm, sm, d, n in worst))
    return rows


if __name__ == "__main__":
    main()
