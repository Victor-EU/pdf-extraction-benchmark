#!/usr/bin/env python3
"""Score the DPT-2 A/B with the CANONICAL structure-aware fair-total judge.

Reuses the byte-identical rubric (PROMPT_HEAD + schema) from score_fair_total_structure so the
numbers are comparable to the headline. On each SOTER subset page it grades, BLIND and SHUFFLED:
  the 8 existing vendors (for calibration context)  +
  landingai_dpt2_chunks (DPT-2, same reducer as legacy)  +
  landingai_dpt2        (DPT-2 native markdown)
so a single judge call yields legacy-LA, dpt2-chunks and dpt2-native side by side. The two LA
deltas attribute the change to MODEL (legacy -> dpt2_chunks) vs OUTPUT FORMAT (dpt2_chunks ->
native). Weighted aggregate uses page_info_weight, exactly like the headline.

Usage: python3 scripts/ab_score_dpt2.py
Output: results/_ab_dpt2_judging.json + a printed table
"""
import os, sys, json, time, random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score_fair_total_structure as S
from build_vendor_md import load_pages

AB = json.load(open("ground_truth/landingai_dpt2_ab/extract.json"))
GT = {(r["doc"], r["page"]): r.get("md", "")
      for r in json.load(open("results/_gt_markdown.json"))}

EXTRA = {"landingai_dpt2_chunks", "landingai_dpt2"}
BASE_VENDORS = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
                "landingai", "llamaparse", "pymupdf", "tesseract"]
ALL = BASE_VENDORS + ["landingai_dpt2_chunks", "landingai_dpt2"]


def build_vendor_md():
    vm = {vd: load_pages(vd) for vd in BASE_VENDORS}
    vm["landingai_dpt2_chunks"] = {(r["doc"], r["page"]): r["chunk_md"] for r in AB}
    vm["landingai_dpt2"] = {(r["doc"], r["page"]): r["native_md"] for r in AB}
    return vm


def judge_page(doc, page, gt_md, vendor_md):
    """Same mechanics as S.judge_page but over the extended ALL vendor list."""
    rnd = random.Random(f"ab:{doc}:{page}")
    order = ALL[:]; rnd.shuffle(order)
    letters = S.LETTERS[:len(order)]
    mapping = dict(zip(letters, order))
    blocks = [S.PROMPT_HEAD,
              f"\n===== GROUND TRUTH (page reference) =====\n{(gt_md or '')[:S.GT_CAP]}"]
    for L in letters:
        blob = (vendor_md[mapping[L]].get((doc, page), "") or "(no extraction)")[:S.VEND_CAP]
        blocks.append(f"\n===== EXTRACTION {L} =====\n{blob}")
    text = "\n".join(blocks)
    fmt = {"format": {"type": "json_schema", "name": "fair_total_structure", "strict": True,
                      "schema": S.schema(letters)}}
    last = None
    for attempt in range(4):
        try:
            r = S.client().responses.create(model=S.MODEL, reasoning={"effort": "low"},
                                            input=[{"role": "user", "content":
                                                    [{"type": "input_text", "text": text}]}],
                                            text=fmt, max_output_tokens=4000)
            obj = json.loads(r.output_text)
            cost = (r.usage.input_tokens * S.PRICE_IN + r.usage.output_tokens * S.PRICE_OUT) / 1e6
            scores = {mapping[L]: obj["scores"][L] for L in letters}
            return {"doc": doc, "page": page, "weight": obj["page_info_weight"],
                    "scores": scores, "cost_usd": round(cost, 6)}
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    return {"doc": doc, "page": page, "error": str(last), "scores": {}}


def main():
    vm = build_vendor_md()
    pages = [(r["doc"], r["page"], r["cat"]) for r in AB]
    print(f"DPT-2 A/B judge: {len(pages)} pages, gpt-5, vs {len(ALL)} vendors\n")
    out = []
    for doc, page, cat in pages:
        res = judge_page(doc, page, GT.get((doc, page), ""), vm)
        res["cat"] = cat
        out.append(res)
        sc = res.get("scores", {})
        def g(v): return sc.get(v, {}).get("info_recall", "-")
        print(f"  p{page:<4} {cat:<14} w={res.get('weight','-'):<3} "
              f"legacy={g('landingai'):<4} dpt2_chunks={g('landingai_dpt2_chunks'):<4} "
              f"dpt2_native={g('landingai_dpt2'):<4}", flush=True)
    json.dump(out, open("results/_ab_dpt2_judging.json", "w"), indent=2)

    # weighted aggregates (same Sigma recall*weight / Sigma weight as the headline)
    def agg(vendor, field):
        num = den = 0
        for r in out:
            w = r.get("weight") or 0
            s = r.get("scores", {}).get(vendor)
            if s is None or not w:
                continue
            num += s[field] * w; den += w
        return (num / den) if den else float("nan")

    print("\n=== WEIGHTED FAIR-TOTAL (SOTER chart-weighted subset, gpt-5 judge) ===")
    print(f"{'vendor':<24}{'info_recall':>12}{'unsupported':>12}")
    focus = ["landingai", "landingai_dpt2_chunks", "landingai_dpt2",
             "gemini_flash", "llamaparse", "pymupdf"]
    for v in focus:
        print(f"{v:<24}{agg(v,'info_recall'):>12.1f}{agg(v,'unsupported'):>12.1f}")
    lo = agg("landingai", "info_recall")
    ch = agg("landingai_dpt2_chunks", "info_recall")
    na = agg("landingai_dpt2", "info_recall")
    print("\n--- DPT-2 deltas (info_recall, pp) ---")
    print(f"  MODEL  (legacy -> dpt2 chunks) : {ch - lo:+.1f}")
    print(f"  FORMAT (dpt2 chunks -> native) : {na - ch:+.1f}")
    print(f"  TOTAL  (legacy -> dpt2 native) : {na - lo:+.1f}")
    print(f"\ncost ${sum(r.get('cost_usd',0) for r in out):.2f}")


if __name__ == "__main__":
    main()
