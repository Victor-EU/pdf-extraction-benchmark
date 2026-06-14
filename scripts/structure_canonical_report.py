#!/usr/bin/env python3
"""Compare the NEW structure-aware canonical fair-total vs the preserved content-recall rubric.

For each judge family: structure-aware headline (own weights), content headline (own weights),
and the ISOLATED rubric delta (content-run weights held fixed, swap only recall) so the change is
not confounded by the judge's weight re-roll. Also unsupported (fidelity) under each rubric, since
the structure rubric counts misbindings as contradictions.
"""
import json, sys
sys.path.insert(0, "scripts")
from build_vendor_md import VENDORS

DISP = {"gemini_flash": "Gemini 3.5 Flash", "gemini_flash_lite": "Gemini 3.1 Flash-Lite",
        "llamaparse": "LlamaParse (agentic)", "landingai": "Landing AI", "pymupdf": "PyMuPDF",
        "tesseract": "Tesseract", "gpt5_file": "gpt-5 file ◆", "gpt5_image": "gpt-5 image ◆"}
ORDER = ["gemini_flash", "gpt5_image", "gpt5_file", "llamaparse", "gemini_flash_lite",
         "landingai", "pymupdf", "tesseract"]


def wmean(rows, v, field="info_recall", weights_from=None):
    """Weighted mean of `field` for vendor v. weights_from: dict (doc,page)->weight to fix weights."""
    num = den = 0.0
    for r in rows:
        s = r["scores"].get(v)
        if not s or s.get(field) is None:
            continue
        w = (weights_from[(r["doc"], r["page"])] if weights_from else (r.get("weight", 1) or 0))
        num += s[field] * w; den += w
    return num / den if den else None


def family(label, struct_path, content_path):
    st = json.load(open(struct_path))
    ct = json.load(open(content_path))
    cw = {(r["doc"], r["page"]): (r.get("weight", 1) or 0) for r in ct}  # fixed content weights
    print(f"\n===== {label} judge =====")
    print(f"{'Vendor':24} {'content':>8} {'struct':>7} {'Δ(fixed-w)':>11} {'unsup↑':>7}")
    print("-" * 62)
    res = []
    for v in ORDER:
        c = wmean(ct, v); s = wmean(st, v)
        # isolated delta: structure recall on fixed content weights minus content recall (same weights)
        s_fw = wmean(st, v, weights_from=cw); c_fw = wmean(ct, v, weights_from=cw)
        d = s_fw - c_fw
        us_c = wmean(ct, v, field="unsupported"); us_s = wmean(st, v, field="unsupported")
        res.append((v, c, s, d, us_c, us_s))
        print(f"{DISP[v]:24} {c:8.1f} {s:7.1f} {d:+11.1f} {us_c:.0f}→{us_s:.0f}")
    real = [r for r in res if "gpt5" not in r[0]]
    print("  content rank: ", " > ".join(f"{DISP[v].split(' (')[0]} {c:.0f}" for v, c, s, d, a, b in sorted(real, key=lambda x: -x[1])))
    print("  STRUCT  rank: ", " > ".join(f"{DISP[v].split(' (')[0]} {s:.0f}" for v, c, s, d, a, b in sorted(real, key=lambda x: -x[2])))
    return res


def main():
    family("gpt-5", "results/_fair_total_judging.json", "results/_fair_total_judging_content.json")
    family("Gemini", "results/_fair_total_judging_gemini_v2.json",
           "results/_fair_total_judging_gemini_v2_content.json")


if __name__ == "__main__":
    main()
