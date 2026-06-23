#!/usr/bin/env python3
"""Score the OCR-4 input A/B with the CANONICAL structure-aware fair-total judge.

Reuses the byte-identical rubric/schema from score_fair_total_structure so numbers are on the
headline scale. On each sampled page it grades, BLIND and SHUFFLED, the 8 base vendors (for
calibration context) + mistral_png + mistral_pdf, so one judge call yields both OCR-4 arms side
by side. Weighted aggregate uses page_info_weight, exactly like the headline.

Usage: ./.venv-mistral/bin/python scripts/ab_score_mistral_input.py
Output: results/_ab_mistral_input_judging.json + a printed table
"""
import os, sys, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score_fair_total_structure as S
from build_vendor_md import load_pages

AB = json.load(open("ground_truth/mistral_ab/extract.json"))
GT = {(r["doc"], r["page"]): r.get("md", "")
      for r in json.load(open("results/_gt_markdown.json"))}
BASE = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
        "landingai", "llamaparse", "pymupdf", "tesseract"]
ALL = BASE + ["mistral_png", "mistral_pdf"]


def vendor_md():
    vm = {vd: load_pages(vd) for vd in BASE}
    vm["mistral_png"] = {(r["doc"], r["page"]): r["png_md"] for r in AB}
    vm["mistral_pdf"] = {(r["doc"], r["page"]): r["pdf_md"] for r in AB}
    return vm


def judge_page(doc, page, gt_md, vm):
    rnd = random.Random(f"abms:{doc}:{page}")
    order = ALL[:]; rnd.shuffle(order)
    letters = S.LETTERS[:len(order)]
    mapping = dict(zip(letters, order))
    blocks = [S.PROMPT_HEAD, f"\n===== GROUND TRUTH (page reference) =====\n{(gt_md or '')[:S.GT_CAP]}"]
    for L in letters:
        blob = (vm[mapping[L]].get((doc, page), "") or "(no extraction)")[:S.VEND_CAP]
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
    vm = vendor_md()
    out = []
    print(f"OCR-4 input A/B judge: {len(AB)} pages, gpt-5, vs {len(ALL)} vendors\n")
    for r in AB:
        doc, page, cat = r["doc"], r["page"], r["cat"]
        res = judge_page(doc, page, GT.get((doc, page), ""), vm)
        res["cat"] = cat
        out.append(res)
        sc = res.get("scores", {})
        def g(v): return sc.get(v, {}).get("info_recall", "-")
        print(f"  {doc[:22]:<22} p{page:<4} {cat:<14} w={res.get('weight','-'):<3} "
              f"png={g('mistral_png'):<4} pdf={g('mistral_pdf'):<4}", flush=True)
    json.dump(out, open("results/_ab_mistral_input_judging.json", "w"), indent=2)

    def agg(vendor, field, cat=None):
        num = den = 0
        for r in out:
            if cat and r.get("cat") != cat:
                continue
            w = r.get("weight") or 0
            s = r.get("scores", {}).get(vendor)
            if s is None or not w:
                continue
            num += s[field] * w; den += w
        return (num / den) if den else float("nan")

    print("\n=== WEIGHTED FAIR-TOTAL (A/B sample, gpt-5 judge) ===")
    print(f"{'vendor':<16}{'recall':>9}{'unsup':>8}")
    for v in ["mistral_png", "mistral_pdf", "gemini_flash", "landingai", "pymupdf"]:
        print(f"{v:<16}{agg(v,'info_recall'):>9.1f}{agg(v,'unsupported'):>8.1f}")
    png, pdf = agg("mistral_png", "info_recall"), agg("mistral_pdf", "info_recall")
    print(f"\n--- input delta (PDF - PNG, info_recall pp): {pdf - png:+.1f} ---")
    print("--- per-category (recall: png / pdf) ---")
    for cat in ["Text", "Table", "Mixed", "Chart/Diagram"]:
        print(f"  {cat:<14} png={agg('mistral_png','info_recall',cat):5.1f}  "
              f"pdf={agg('mistral_pdf','info_recall',cat):5.1f}")
    print(f"\ncost ${sum(r.get('cost_usd',0) for r in out):.2f}")


if __name__ == "__main__":
    main()
