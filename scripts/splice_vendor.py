#!/usr/bin/env python3
"""Splice a NEWLY-ADDED vendor's score column into the canonical judging JSONs, with canonical page
weights FROZEN and every existing vendor left byte-identical. Generalization of splice_liteparse.py
(ADD, not swap) to an arbitrary vendor — used to add Mistral OCR 4 as the 8th vendor.

The N-vendor re-judge grades all vendors together (proper relative calibration) and re-rolls its own
page weights, but we DISCARD those weights and splice ONLY the new vendor's score column into
canonical, keeping canonical's GT-determined weights and every other vendor's published score
unchanged. The new vendor's score therefore comes from a run where it was graded in-context against
the others; the published numbers do not move.

Validity check = the existing vendors' AGGREGATE (computed under canonical weights) should not be
GROSSLY distorted between the canonical run and the N-vendor run — proving that adding the new
extraction did not break how the judge grades the others. IMPORTANT: this corpus is **n = 7 pages**,
so per-page judge variance dominates and a few points of aggregate drift are EXPECTED and meaningless
(Insurance memory: "n=7 too few for stable aggregates"). The gate is therefore loose (gross-distortion
guard, not a stability proof); freezing canonical is precisely what protects the published numbers.

Two metric families, identical splice, different validation read-out:
  - fair-total files: scores = {info_recall, unsupported}; validate on info_recall.
  - spatial files:    scores = {field/checkbox/table _binding + _present}; validate on the composite.

Re-judges must have been produced with LA_DPT2=1 (canonical serves the `landingai` slot from the
DPT-2 extract). Usage:
  python3 scripts/splice_vendor.py mistral            # validate + before/after report
  python3 scripts/splice_vendor.py mistral --splice   # also write canonical (archives originals)
"""
import os, sys, json, shutil

VENDOR = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
if not VENDOR:
    sys.exit("usage: splice_vendor.py <vendor> [--splice]")
# per-vendor re-judge filename suffix (liteparse historically used `lp`)
SUFFIX = {"liteparse": "lp"}.get(VENDOR, VENDOR)

# (display name, canonical path, N-vendor re-judge path, family)
FAMILIES = [
    ("gpt-5 structure",  "results/_fair_total_judging.json",
                         f"results/_fair_total_judging_{SUFFIX}.json", "fairtotal"),
    ("gpt-5 content",    "results/_fair_total_judging_content.json",
                         f"results/_fair_total_judging_content_{SUFFIX}.json", "fairtotal"),
    ("gemini structure", "results/_fair_total_judging_gemini_v2.json",
                         f"results/_fair_total_judging_gemini_v2_{SUFFIX}.json", "fairtotal"),
    ("gpt-5 spatial",    "results/_spatial_judging.json",
                         f"results/_spatial_judging_{SUFFIX}.json", "spatial"),
    ("gemini spatial",   "results/_spatial_judging_gemini.json",
                         f"results/_spatial_judging_gemini_{SUFFIX}.json", "spatial"),
]
# existing (already-canonical) vendors whose aggregate must stay stable; the new VENDOR is excluded
CANON_VENDORS = [v for v in
                 ["gpt5_image", "gemini_flash", "landingai", "llamaparse", "pymupdf", "tesseract", "liteparse"]
                 if v != VENDOR]
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


def validate(canon, runN, family):
    print("  VALIDATION — existing vendors under canonical weights (|Δ| < %.0f, n=7 noise gate):" % DRIFT_GATE)
    ok, worst = True, 0.0
    for v in CANON_VENDORS:
        a = wagg(canon, v, canon, family); b = wagg(canon, v, runN, family)
        d = abs(a - b); worst = max(worst, d)
        if d >= DRIFT_GATE:
            ok = False
        print(f"    {v:<14} canon={a:5.1f}  N-vend={b:5.1f}  Δ={b-a:+5.1f}{'' if d < DRIFT_GATE else '  <-- DRIFT'}")
    print(f"    -> worst aggregate drift {worst:.1f}pp ({'PASS' if ok else 'FAIL'})")
    return ok


def report(name, canon, runN, family):
    print(f"\n===== {name} ({family}) =====")
    ok = validate(canon, runN, family)
    rec = wagg(canon, VENDOR, runN, family)
    print(f"  NEW vendor '{VENDOR}': aggregate {'info_recall' if family=='fairtotal' else 'SPATIAL'}={rec:.1f}")
    if family == "fairtotal":
        u = d = 0.0
        for k, r in canon.items():
            w = r.get("weight") or 0
            s = runN.get(k, {}).get("scores", {}).get(VENDOR)
            if w and s is not None and s.get("unsupported") is not None:
                u += s["unsupported"] * w; d += w
        print(f"           unsupported={u/d if d else float('nan'):.1f}")
    return ok


def splice_into(canon_path, runN_path):
    canon = json.load(open(canon_path))
    runN = load(runN_path)
    n = 0
    for r in canon:
        src = runN.get((r["doc"], r["page"]), {}).get("scores", {}).get(VENDOR)
        if src is not None and "scores" in r:
            r["scores"][VENDOR] = src; n += 1
    arch = f"results/pre_{VENDOR}_archive"
    os.makedirs(arch, exist_ok=True)
    shutil.copy(canon_path, os.path.join(arch, os.path.basename(canon_path)))
    json.dump(canon, open(canon_path, "w"), indent=2)
    print(f"  spliced {VENDOR} into {n} pages -> {canon_path}  (original archived in {arch}/)")


def main():
    do_splice = "--splice" in sys.argv
    # families to splice even though they tripped the gate, e.g. --force="gemini spatial".
    # Use ONLY for a drift that is documented n=7 judge-noise on vendors OTHER than the new one
    # (the new vendor's own column must be cross-family-corroborated). Splice still freezes canonical,
    # so no existing published number moves regardless.
    forced = set()
    for a in sys.argv[1:]:
        if a.startswith("--force="):
            forced |= {x.strip() for x in a.split("=", 1)[1].split(",") if x.strip()}
    present = []   # (name, cp, rp, passed)
    for name, cp, rp, fam in FAMILIES:
        if not os.path.exists(rp):
            print(f"\n{name}: re-judge {rp} not found — skipping"); continue
        canon, runN = load(cp), load(rp)
        present.append((name, cp, rp, report(name, canon, runN, fam)))
    if not do_splice:
        print("\n(report only — pass --splice to write canonical)"); return
    print("\n--- SPLICING into canonical (per-family; canonical weights stay FROZEN) ---")
    for name, cp, rp, passed in present:
        if passed:
            splice_into(cp, rp)
        elif name in forced:
            print(f"  [FORCED] {name}: gate tripped but FORCED by operator "
                  f"(documented n=7 noise on other vendors; new vendor column corroborated).")
            splice_into(cp, rp)
        else:
            print(f"  [HELD OUT] {name}: gate FAILED and not in --force; canonical left unchanged "
                  f"for this family. Inspect, then re-run with --force=\"{name}\" if it is documented noise.")
    print("Done. Re-run fair_total_report.py + spatial_report.py to regenerate the tables.")


if __name__ == "__main__":
    main()
