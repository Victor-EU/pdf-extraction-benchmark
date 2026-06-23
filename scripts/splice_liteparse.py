#!/usr/bin/env python3
"""Splice the NEWLY-ADDED LiteParse column into the canonical judging JSONs, with canonical page
weights FROZEN and the existing 6 vendors left byte-identical.

Mirrors the Finance benchmark's splice_vendor.py (ADD, not swap). The 7-vendor re-judge grades all
vendors together (proper relative calibration) and re-rolls its own page weights, but we DISCARD
those weights and splice ONLY LiteParse's score column into canonical, keeping canonical's
GT-determined weights and every other vendor's published score unchanged. The new vendor's score
therefore comes from a run where it was graded in-context against the others; the published numbers
do not move.

Validity check = the existing vendors' AGGREGATE (computed under canonical weights) should not be
GROSSLY distorted between the canonical run and the 7-vendor run — proving that adding LiteParse's
extraction did not break how the judge grades the others (e.g. via a prompt/contamination bug).
IMPORTANT: this corpus is **n = 7 pages**, so per-page judge variance dominates and a few points of
aggregate drift are EXPECTED and meaningless (the Insurance memory: "n=7 too few for stable
aggregates"). The gate is therefore loose (gross-distortion guard, not a stability proof); freezing
canonical is precisely what protects the published numbers from that noise.

Two metric families, identical splice, different validation read-out:
  - fair-total files: scores = {info_recall, unsupported}; validate on info_recall.
  - spatial files:    scores = {field/checkbox/table _binding + _present}; validate on the composite.

Re-judges must have been produced with LA_DPT2=1 (canonical serves the `landingai` slot from the
DPT-2 extract). Usage:
  python3 scripts/splice_liteparse.py            # validate + before/after report
  python3 scripts/splice_liteparse.py --splice   # also write canonical (archives originals)
"""
import os, sys, json, shutil

VENDOR = "liteparse"
# (display name, canonical path, 7-vendor re-judge path, family)
FAMILIES = [
    ("gpt-5 structure",  "results/_fair_total_judging.json",
                         "results/_fair_total_judging_lp.json", "fairtotal"),
    ("gpt-5 content",    "results/_fair_total_judging_content.json",
                         "results/_fair_total_judging_content_lp.json", "fairtotal"),
    ("gemini structure", "results/_fair_total_judging_gemini_v2.json",
                         "results/_fair_total_judging_gemini_v2_lp.json", "fairtotal"),
    ("gpt-5 spatial",    "results/_spatial_judging.json",
                         "results/_spatial_judging_lp.json", "spatial"),
    ("gemini spatial",   "results/_spatial_judging_gemini.json",
                         "results/_spatial_judging_gemini_lp.json", "spatial"),
]
CANON_VENDORS = ["gpt5_image", "gemini_flash", "landingai", "llamaparse", "pymupdf", "tesseract"]
DRIFT_GATE = 10.0  # loose gross-distortion guard appropriate to n=7 (see module docstring)
SPW = {"field_value_binding": 1.0, "checkbox_state": 1.0, "table_cell_binding": 0.8}


def load(path):
    return {(r["doc"], r["page"]): r for r in json.load(open(path))}


def composite(s):
    num = den = 0.0
    for k, pres in (("field_value_binding", "field_present"),
                    ("checkbox_state", "checkbox_present"),
                    ("table_cell_binding", "table_present")):
        if s and s.get(pres):
            num += s[k] * SPW[k]; den += SPW[k]
    return (num / den) if den else None


def score_of(s, family):
    if s is None:
        return None
    return s.get("info_recall") if family == "fairtotal" else composite(s)


def wagg(weights_index, vendor, score_src, family):
    """Σ score*weight / Σ weight; weights from weights_index, per-vendor score from score_src."""
    num = den = 0.0
    for k, r in weights_index.items():
        w = r.get("weight") or 0
        val = score_of(score_src.get(k, {}).get("scores", {}).get(vendor), family)
        if not w or val is None:
            continue
        num += val * w; den += w
    return num / den if den else float("nan")


def validate(canon, run7, family):
    print("  VALIDATION — existing vendors under canonical weights (|Δ| < %.0f, n=7 noise gate):" % DRIFT_GATE)
    ok, worst = True, 0.0
    for v in CANON_VENDORS:
        a = wagg(canon, v, canon, family); b = wagg(canon, v, run7, family)
        d = abs(a - b); worst = max(worst, d)
        if d >= DRIFT_GATE:
            ok = False
        print(f"    {v:<14} canon={a:5.1f}  7-vend={b:5.1f}  Δ={b-a:+5.1f}{'' if d < DRIFT_GATE else '  <-- DRIFT'}")
    print(f"    -> worst aggregate drift {worst:.1f}pp ({'PASS' if ok else 'FAIL'})")
    return ok


def report(name, canon, run7, family):
    print(f"\n===== {name} ({family}) =====")
    ok = validate(canon, run7, family)
    rec = wagg(canon, VENDOR, run7, family)
    print(f"  NEW vendor '{VENDOR}': aggregate {'info_recall' if family=='fairtotal' else 'SPATIAL'}={rec:.1f}"
          + (f"  unsupported={wagg(canon, VENDOR, run7, 'unsup_dummy') if False else ''}" if False else ""))
    if family == "fairtotal":
        u = 0.0; d = 0.0
        for k, r in canon.items():
            w = r.get("weight") or 0
            s = run7.get(k, {}).get("scores", {}).get(VENDOR)
            if w and s is not None and s.get("unsupported") is not None:
                u += s["unsupported"] * w; d += w
        print(f"           unsupported={u/d if d else float('nan'):.1f}")
    return ok


def splice_into(canon_path, run7_path):
    canon = json.load(open(canon_path))
    run7 = load(run7_path)
    n = 0
    for r in canon:
        src = run7.get((r["doc"], r["page"]), {}).get("scores", {}).get(VENDOR)
        if src is not None and "scores" in r:
            r["scores"][VENDOR] = src; n += 1
    arch = "results/pre_liteparse_archive"
    os.makedirs(arch, exist_ok=True)
    shutil.copy(canon_path, os.path.join(arch, os.path.basename(canon_path)))
    json.dump(canon, open(canon_path, "w"), indent=2)
    print(f"  spliced {VENDOR} into {n} pages -> {canon_path}  (original archived in {arch}/)")


def main():
    do_splice = "--splice" in sys.argv
    all_ok = True
    present = []
    for name, cp, rp, fam in FAMILIES:
        if not os.path.exists(rp):
            print(f"\n{name}: re-judge {rp} not found — skipping"); continue
        canon, run7 = load(cp), load(rp)
        present.append((cp, rp))
        all_ok &= report(name, canon, run7, fam)
    if do_splice:
        if not all_ok:
            print("\nABORT splice: drift exceeded the gross-distortion gate. Inspect before forcing."); sys.exit(1)
        print("\n--- SPLICING into canonical (validation passed) ---")
        for cp, rp in present:
            splice_into(cp, rp)
        print("Done. Re-run fair_total_report.py + spatial_report.py to regenerate the tables.")
    else:
        print("\n(report only — pass --splice to write canonical)")


if __name__ == "__main__":
    main()
