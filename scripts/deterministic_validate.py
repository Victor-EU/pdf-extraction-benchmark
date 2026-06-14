#!/usr/bin/env python3
"""DETERMINISTIC VALIDATOR (shipped) — a zero-LLM, zero-variance cross-check on the headline.

NOT a replacement for the LLM judge. Three jobs, each scoped to where deterministic matching is
trustworthy on this born-digital corpus (numbers are an exact oracle):

  1. TIERING corroboration on TABLE pages — the "structure tax" (numeric_recall - binding_recall)
     reproduces the judge's structure tiering and the text-dumper collapse WITHOUT the model that
     also authored/judged the GT. (Scoped to tables: TEXT is confounded by OCR token-mangling and
     the judge's reading-order sensitivity, which binding cannot see — reported as a diagnostic.)
  2. NUMERIC-FIDELITY FLOOR on all number-bearing pages — an oracle-backed LOWER bound on how many
     of the GT's printed numbers each vendor preserved (exact normalized match => no false credit).
  3. JUDGE-DISAGREEMENT worklist — gated TABLE pages where deterministic and judge diverge, the
     place the next measurement bug hides (this harness already caught one: the vendor_md ## split).

Atom primitives (page_atoms, binding_recall) are imported from poc_binding_score so the two stay
byte-identical. Output: results/_deterministic_scores.json  (consumed by deterministic_report.py)
"""
import os, sys, json
from statistics import mean

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import poc_binding_score as poc

# minimum DISTINCT labeled numeric atoms a GT page must hold for its binding_recall to be reported.
# Drops genuinely number-sparse pages (Cover/Divider median 2) where a couple of incidental numbers
# would dominate; keeps 117/128 real tables (median 44). p131-type pages (numbers incidental to a
# non-numeric matrix) pass the count gate but are diluted in aggregates and surfaced by job 3.
GATE = int(os.environ.get("DET_GATE", "5"))
VENDORS = ["gemini_flash", "gpt5_image", "landingai", "llamaparse", "pymupdf", "tesseract"]


def main():
    gt = {(r["doc"], r["page"]): r.get("md", "")
          for r in json.load(open("results/_gt_markdown.json"))}
    cats = {(e["doc"], e["page"]): e["final_label"]
            for e in json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))["pages"]}
    js = {(r["doc"], r["page"]): r for r in json.load(open("results/_fair_total_judging.json"))}
    jc = {(r["doc"], r["page"]): r
          for r in json.load(open("results/_fair_total_judging_content.json"))}
    vmd = {v: poc._vendor_pages(v) for v in VENDORS}

    # precompute GT atoms + per-page labeled-atom count (vendor-independent, drives the gate)
    gt_at = {}
    for k, md in gt.items():
        gn, ga = poc.page_atoms(md)
        labeled = {(n, L) for n, L in ga if L}
        gt_at[k] = {"gnums": gn, "gatoms": ga, "n_labeled": len(labeled)}

    out = []
    for v in VENDORS:
        for k, g in gt_at.items():
            if len(g["gnums"]) < 3:          # not number-bearing → numeric metrics meaningless
                continue
            vp = vmd[v].get(k, "")
            vn, va = poc.page_atoms(vp)
            nrec = len(g["gnums"] & vn) / len(g["gnums"])
            gated = g["n_labeled"] >= GATE
            brec = poc.binding_recall(g["gatoms"], vn, va) if gated else None
            jr = js.get(k, {})
            cr = jc.get(k, {})
            out.append({
                "v": v, "doc": k[0], "page": k[1], "cat": cats.get(k, "?"),
                "n_labeled": g["n_labeled"], "gated": gated,
                "numeric_recall": round(nrec, 4),
                "binding_recall": round(brec, 4) if brec is not None else None,
                "judge_struct": jr.get("scores", {}).get(v, {}).get("info_recall"),
                "judge_unsupported": jr.get("scores", {}).get(v, {}).get("unsupported"),
                "judge_content": cr.get("scores", {}).get(v, {}).get("info_recall"),
                "weight": jr.get("weight"),
            })

    json.dump(out, open("results/_deterministic_scores.json", "w"), indent=2)
    n_gated = len({(r["doc"], r["page"]) for r in out if r["gated"]})
    n_all = len({(r["doc"], r["page"]) for r in out})
    print(f"scored {len(out)} vendor-pages over {n_all} number-bearing pages "
          f"({n_gated} pass gate>={GATE}); -> results/_deterministic_scores.json")


if __name__ == "__main__":
    main()
