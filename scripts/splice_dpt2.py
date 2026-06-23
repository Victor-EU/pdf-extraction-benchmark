#!/usr/bin/env python3
"""Validate the DPT-2 re-judge, report legacy-vs-DPT-2, and (with --splice) splice DPT-2 into the
canonical fair-total JSONs.

The DPT-2 re-judge (LA_DPT2=1) re-ran BOTH judge families over all 599 pages with byte-identical
prompts EXCEPT Landing AI's extraction block (legacy -> DPT-2), same seed/shuffle/other-7 vendors.
Therefore:
  - the other 7 vendors' scores in the DPT-2 run should match canonical within judge noise
    (VALIDATION — proves the swap is clean and the LA delta is controlled), and
  - DPT-2's LA score is directly comparable to canonical legacy-LA, so splicing DPT-2 into LA's
    slot of the canonical JSONs (keeping canonical weight + other 7) is exact.

Usage:
  python3 scripts/splice_dpt2.py             # validate + before/after report only
  python3 scripts/splice_dpt2.py --splice    # also archive legacy + write spliced canonical
"""
import os, sys, json, shutil

FAMILIES = {
    "gpt-5":  ("results/_fair_total_judging.json",          "results/_fair_total_judging_dpt2.json"),
    "gemini": ("results/_fair_total_judging_gemini_v2.json","results/_fair_total_judging_gemini_v2_dpt2.json"),
}
VENDORS = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
           "landingai", "llamaparse", "pymupdf", "tesseract"]
OTHERS = [v for v in VENDORS if v != "landingai"]
DRIFT_GATE = 1.5  # max acceptable AGGREGATE fair-total drift on the untouched vendors.
# NB: the right validity test is AGGREGATE stability, not per-page |Δ|. Per-page judge variance is
# large (±20-25pp, measured in the A/B replicate study) and averages out; what must hold is that
# swapping LA's block doesn't systematically shift the other 7 vendors' weighted fair-total.


def load(path):
    return {(r["doc"], r["page"]): r for r in json.load(open(path))}


def wfair(index, vendor, score_src=None, field="info_recall"):
    """Σ recall*weight / Σ weight. score_src lets LA pull from a different index than `index`."""
    num = den = 0.0
    for k, r in index.items():
        w = r.get("weight") or 0
        src = (score_src or index).get(k, {})
        s = src.get("scores", {}).get(vendor)
        if not w or s is None:
            continue
        num += s[field] * w; den += w
    return num / den if den else float("nan")


def validate(canon, dpt2):
    """Splice validity = AGGREGATE fair-total of the untouched 7 must be stable between the
    canonical run and the DPT-2 run (only LA's block differs). Per-page noise is irrelevant."""
    print("  VALIDATION — untouched vendors' AGGREGATE fair-total must be stable (|Δ| < %.1f):" % DRIFT_GATE)
    ok = True
    worst = 0.0
    for v in OTHERS:
        a = wfair(canon, v); b = wfair(dpt2, v)
        d = abs(a - b); worst = max(worst, d)
        flag = "" if d < DRIFT_GATE else "  <-- DRIFT"
        if d >= DRIFT_GATE:
            ok = False
        print(f"    {v:<20} canon={a:5.1f}  dpt2run={b:5.1f}  Δ={b-a:+5.2f}{flag}")
    print(f"    -> worst aggregate drift {worst:.2f}pp ({'PASS' if ok else 'FAIL'})")
    return ok


def docs_of(index):
    return sorted({k[0] for k in index})


def report(name, canon, dpt2):
    print(f"\n===== {name} judge =====")
    val_ok = validate(canon, dpt2)
    print("\n  FAIR-TOTAL info_recall (weight = canonical, GT-determined):")
    print(f"    {'scope':<40}{'legacy LA':>11}{'DPT-2 LA':>11}{'Δ':>8}")
    scopes = [("CORPUS", canon, dpt2)]
    legacy_c = wfair(canon, "landingai")
    dpt2_c = wfair(canon, "landingai", score_src=dpt2)
    print(f"    {'CORPUS':<40}{legacy_c:>11.1f}{dpt2_c:>11.1f}{dpt2_c-legacy_c:>+8.1f}")
    for d in docs_of(canon):
        ck = {k: v for k, v in canon.items() if k[0] == d}
        dk = {k: v for k, v in dpt2.items() if k[0] == d}
        lo = wfair(ck, "landingai"); hi = wfair(ck, "landingai", score_src=dk)
        print(f"    {d[:40]:<40}{lo:>11.1f}{hi:>11.1f}{hi-lo:>+8.1f}")
    lo_u = wfair(canon, "landingai", field="unsupported")
    hi_u = wfair(canon, "landingai", score_src=dpt2, field="unsupported")
    print(f"    {'unsupported (lower better)':<40}{lo_u:>11.1f}{hi_u:>11.1f}{hi_u-lo_u:>+8.1f}")
    return val_ok


def splice_into(canon_path, dpt2_path):
    canon = json.load(open(canon_path))
    dpt2 = load(dpt2_path)
    n = 0
    for r in canon:
        k = (r["doc"], r["page"])
        src = dpt2.get(k, {}).get("scores", {}).get("landingai")
        if src is not None and "scores" in r:
            r["scores"]["landingai"] = src; n += 1
    arch_dir = "results/legacy_la_archive"
    os.makedirs(arch_dir, exist_ok=True)
    shutil.copy(canon_path, os.path.join(arch_dir, os.path.basename(canon_path)))
    json.dump(canon, open(canon_path, "w"), indent=2)
    print(f"  spliced {n} pages -> {canon_path}  (legacy archived in {arch_dir}/)")


def main():
    do_splice = "--splice" in sys.argv
    all_ok = True
    for name, (cp, dp) in FAMILIES.items():
        if not os.path.exists(dp):
            print(f"\n{name}: DPT-2 run {dp} not found — skipping"); continue
        canon = load(cp); dpt2 = load(dp)
        all_ok &= report(name, canon, dpt2)
    if do_splice:
        if not all_ok:
            print("\nABORT splice: validation drift exceeded gate. Inspect before forcing.")
            sys.exit(1)
        print("\n--- SPLICING into canonical (validation passed) ---")
        for name, (cp, dp) in FAMILIES.items():
            if os.path.exists(dp):
                splice_into(cp, dp)
        print("Done. Re-run fair_total_report.py / by_document.py to regenerate headline tables.")
    else:
        print("\n(report only — pass --splice to write canonical)")


if __name__ == "__main__":
    main()
