#!/usr/bin/env python3
"""Splice a NEWLY-ADDED vendor's column into the canonical fair-total JSONs, with canonical
page weights FROZEN and the existing vendors left byte-identical.

Generalizes splice_dpt2.py from a SWAP (legacy LA -> DPT-2, same 8 vendors) to an ADD (9th vendor).
The re-judge run grades all 9 vendors together (proper relative calibration) and re-rolls its own
page weights, but we DISCARD those weights and splice only the new vendor's recall/unsupported
column into canonical, keeping canonical's GT-determined weights. Validity = the existing vendors'
AGGREGATE fair-total (computed under canonical weights) must be stable between the canonical run and
the 9-vendor run — proving that adding the new extraction did not distort how the judge graded the
others. Per-page judge variance (±20-25pp, measured) is large and irrelevant; only the weighted
aggregate must hold. Same logic, same gate as splice_dpt2.

Usage:
  python3 scripts/splice_vendor.py liteparse              # validate + before/after report
  python3 scripts/splice_vendor.py liteparse --splice     # also write canonical (archives originals)
"""
import os, sys, json, shutil

# (canonical path, 9-vendor re-judge path) per judge family/rubric.
FAMILIES = {
    "gpt-5 structure":  ("results/_fair_total_judging.json",
                         "results/_fair_total_judging_lp.json"),
    "gemini structure": ("results/_fair_total_judging_gemini_v2.json",
                         "results/_fair_total_judging_gemini_v2_lp.json"),
    "gpt-5 content":    ("results/_fair_total_judging_content.json",
                         "results/_fair_total_judging_content_lp.json"),
    "gemini content":   ("results/_fair_total_judging_gemini_v2_content.json",
                         "results/_fair_total_judging_gemini_v2_content_lp.json"),
}
# canonical 8 (the ones that must stay stable); the new vendor is the CLI arg.
CANON_VENDORS = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
                 "landingai", "llamaparse", "pymupdf", "tesseract"]
DRIFT_GATE = 1.5


def load(path):
    return {(r["doc"], r["page"]): r for r in json.load(open(path))}


def wfair(weights_index, vendor, score_src, field="info_recall"):
    """Σ recall*weight / Σ weight, weights from weights_index, scores from score_src."""
    num = den = 0.0
    for k, r in weights_index.items():
        w = r.get("weight") or 0
        s = score_src.get(k, {}).get("scores", {}).get(vendor)
        if not w or s is None:
            continue
        num += s[field] * w; den += w
    return num / den if den else float("nan")


def validate(canon, run9):
    """Existing vendors' aggregate fair-total under CANONICAL weights must match between the
    canonical scores and the 9-vendor-run scores."""
    print("  VALIDATION — existing vendors stable under canonical weights (|Δ| < %.1f):" % DRIFT_GATE)
    ok, worst = True, 0.0
    for v in CANON_VENDORS:
        a = wfair(canon, v, canon); b = wfair(canon, v, run9)
        d = abs(a - b); worst = max(worst, d)
        flag = "" if d < DRIFT_GATE else "  <-- DRIFT"
        if d >= DRIFT_GATE:
            ok = False
        print(f"    {v:<18} canon={a:5.1f}  9-vend={b:5.1f}  Δ={b-a:+5.2f}{flag}")
    print(f"    -> worst aggregate drift {worst:.2f}pp ({'PASS' if ok else 'FAIL'})")
    return ok


def report(name, canon, run9, vendor):
    print(f"\n===== {name} =====")
    ok = validate(canon, run9)
    rec = wfair(canon, vendor, run9)
    uns = wfair(canon, vendor, run9, field="unsupported")
    print(f"  NEW vendor '{vendor}': CORPUS info_recall={rec:.1f}  unsupported={uns:.1f}")
    print("  (canonical-weighted; per-doc:)")
    for d in sorted({k[0] for k in canon}):
        ck = {k: v for k, v in canon.items() if k[0] == d}
        r9 = {k: v for k, v in run9.items() if k[0] == d}
        print(f"    {d[:42]:<42}{wfair(ck, vendor, r9):6.1f}")
    return ok


def splice_into(vendor, canon_path, run9_path):
    canon = json.load(open(canon_path))
    run9 = load(run9_path)
    n = 0
    for r in canon:
        k = (r["doc"], r["page"])
        src = run9.get(k, {}).get("scores", {}).get(vendor)
        if src is not None and "scores" in r:
            r["scores"][vendor] = src; n += 1
    arch = "results/pre_liteparse_archive"
    os.makedirs(arch, exist_ok=True)
    shutil.copy(canon_path, os.path.join(arch, os.path.basename(canon_path)))
    json.dump(canon, open(canon_path, "w"), indent=2)
    print(f"  spliced {vendor} into {n} pages -> {canon_path}  (original archived in {arch}/)")


def main():
    if len(sys.argv) < 2:
        print("usage: splice_vendor.py <vendor> [--splice]"); sys.exit(1)
    vendor = sys.argv[1]
    do_splice = "--splice" in sys.argv
    all_ok = True
    present = {}
    for name, (cp, rp) in FAMILIES.items():
        if not os.path.exists(rp):
            print(f"\n{name}: 9-vendor run {rp} not found — skipping"); continue
        canon, run9 = load(cp), load(rp)
        present[name] = (cp, rp)
        all_ok &= report(name, canon, run9, vendor)
    if do_splice:
        if not all_ok:
            print("\nABORT splice: validation drift exceeded gate. Inspect before forcing."); sys.exit(1)
        print("\n--- SPLICING into canonical (validation passed) ---")
        for name, (cp, rp) in present.items():
            splice_into(vendor, cp, rp)
        print("Done. Re-run fair_total_report.py / by_document.py to regenerate headline tables.")
    else:
        print("\n(report only — pass --splice to write canonical)")


if __name__ == "__main__":
    main()
