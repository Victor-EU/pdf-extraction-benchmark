#!/usr/bin/env python3
"""Three-way A/B judge: legacy LA vs DPT-2(PNG) vs DPT-2(PDF page), one blind call per page.

Same canonical structure-aware rubric (gpt-5) as the headline. All three LA variants graded in
the SAME shuffled comparison so input-medium (PNG vs PDF) is isolated cleanly. The 6 other vendors
are kept for calibration context. Output: results/_ab_dpt2_pdf_judging.json + printed table.
"""
import os, sys, json, time, random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score_fair_total_structure as S
from build_vendor_md import load_pages

PNG = json.load(open("ground_truth/landingai_dpt2_ab/extract.json"))
PDF = json.load(open("ground_truth/landingai_dpt2_pdf_ab/extract.json"))
GT = {(r["doc"], r["page"]): r.get("md", "")
      for r in json.load(open("results/_gt_markdown.json"))}

BASE = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
        "landingai", "llamaparse", "pymupdf", "tesseract"]
ALL = BASE + ["landingai_dpt2_png", "landingai_dpt2_pdf"]


def build_vendor_md():
    vm = {vd: load_pages(vd) for vd in BASE}
    vm["landingai_dpt2_png"] = {(r["doc"], r["page"]): r["native_md"] for r in PNG}
    vm["landingai_dpt2_pdf"] = {(r["doc"], r["page"]): r["native_md"] for r in PDF}
    return vm


REP = os.environ.get("REP", "0")  # replicate id varies shuffle+API call to measure judge noise


def judge_page(doc, page, gt_md, vm):
    rnd = random.Random(f"abpdf{REP}:{doc}:{page}")
    order = ALL[:]; rnd.shuffle(order)
    letters = S.LETTERS[:len(order)]
    mapping = dict(zip(letters, order))
    blocks = [S.PROMPT_HEAD,
              f"\n===== GROUND TRUTH (page reference) =====\n{(gt_md or '')[:S.GT_CAP]}"]
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
            return {"doc": doc, "page": page, "weight": obj["page_info_weight"],
                    "scores": {mapping[L]: obj["scores"][L] for L in letters},
                    "cost_usd": round(cost, 6)}
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    return {"doc": doc, "page": page, "error": str(last), "scores": {}}


def main():
    vm = build_vendor_md()
    pages = [(r["doc"], r["page"], r["cat"]) for r in PDF]
    print(f"3-way A/B judge: {len(pages)} pages, gpt-5\n")
    out = []
    for doc, page, cat in pages:
        res = judge_page(doc, page, GT.get((doc, page), ""), vm); res["cat"] = cat
        out.append(res)
        s = res.get("scores", {})
        def g(v): return s.get(v, {}).get("info_recall", "-")
        def u(v): return s.get(v, {}).get("unsupported", "-")
        print(f"  p{page:<4} {cat:<14} w={res.get('weight','-'):<3} "
              f"legacy={g('landingai'):<4} png={g('landingai_dpt2_png'):<4} "
              f"pdf={g('landingai_dpt2_pdf'):<4}  (unsup {u('landingai')}/{u('landingai_dpt2_png')}/{u('landingai_dpt2_pdf')})",
              flush=True)
    json.dump(out, open(f"results/_ab_dpt2_pdf_judging_rep{REP}.json", "w"), indent=2)

    def agg(v, f):
        num = den = 0
        for r in out:
            w = r.get("weight") or 0; sc = r.get("scores", {}).get(v)
            if sc and w:
                num += sc[f] * w; den += w
        return num / den if den else float("nan")

    print("\n=== WEIGHTED FAIR-TOTAL (SOTER subset, gpt-5) ===")
    print(f"{'vendor':<24}{'info_recall':>12}{'unsupported':>12}")
    for v in ["landingai", "landingai_dpt2_png", "landingai_dpt2_pdf",
              "gemini_flash", "llamaparse", "pymupdf"]:
        print(f"{v:<24}{agg(v,'info_recall'):>12.1f}{agg(v,'unsupported'):>12.1f}")
    lo, pn, pd = (agg(x, "info_recall") for x in
                  ["landingai", "landingai_dpt2_png", "landingai_dpt2_pdf"])
    print("\n--- deltas (info_recall, pp) ---")
    print(f"  legacy -> DPT-2 PNG      : {pn - lo:+.1f}")
    print(f"  DPT-2 PNG -> DPT-2 PDF   : {pd - pn:+.1f}  (input medium)")
    print(f"  legacy -> DPT-2 PDF      : {pd - lo:+.1f}  (TOTAL realistic pipeline)")
    print(f"\ncost ${sum(r.get('cost_usd',0) for r in out):.2f}")


if __name__ == "__main__":
    main()
