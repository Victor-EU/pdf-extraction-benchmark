#!/usr/bin/env python3
"""Document-level FAIR TOTAL: how much of each page's real information does a vendor convey,
judged against the GROUND-TRUTH markdown with PARAPHRASE TOLERANCE (a diagram/chart/table
described in different-but-correct words counts as captured).

For each page, a BLIND gpt-5 judge sees the GT transcription + all 8 vendors' full page markdown
(shuffled A-H) and returns, per vendor: info_recall (% of GT info conveyed) and unsupported
(% of the vendor's claims not backed by GT = fidelity flag). It also rates page_info_weight 1-10.

Headline "fair total" = sum(info_recall * weight) / sum(weight) over all 599 pages — a genuine
ratio of total information captured to total information present, density-weighted by the content
itself (NOT a weighted average of arbitrary dimensions).

NOTE: gpt-5 built the GT (same family) so its own cells are an upper bound, reported but flagged
not-comparable. Output: results/_fair_total_judging.json
"""
import os, sys, json, time, glob, random, threading
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from build_vendor_md import VENDORS, load_pages

if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = _l.split("=", 1)[1].strip()

MODEL = "gpt-5"
PRICE_IN, PRICE_OUT = 1.25, 10.0
LETTERS = "ABCDEFGHIJKL"
GT_CAP = int(os.environ.get("FT_GT_CAP", "6000"))
VEND_CAP = int(os.environ.get("FT_VEND_CAP", "6000"))

PROMPT_HEAD = (
"You are a STRICT, BLIND grader of document-extraction COMPLETENESS. Below is a GROUND-TRUTH "
"transcription of ONE page, then several parser extractions of the same page, labeled A, B, C, ...\n\n"
"The GROUND TRUTH lists the page's real information: text, numbers, table cells, chart data points, "
"diagram structure, and labels.\n\n"
"TASK:\n"
"1) page_info_weight (1-10): how much substantive information does this page hold, per the ground "
"truth? 1 = nearly empty (cover/divider, a title only); 5 = a normal text/slide page; 10 = very "
"dense (large data table, multi-series chart, or detailed schematic with many values).\n"
"2) For EACH extraction, grade ONLY against the ground truth's information, and CREDIT EQUIVALENT "
"PHRASING as fully correct: a table, chart, or diagram described in DIFFERENT WORDS that conveys the "
"same facts, numbers and relationships is fully captured. Reward information, NOT verbosity or wording.\n"
"   - info_recall (0-100): what fraction of the ground truth's substantive information (facts, "
"numbers, table cells, chart DATA VALUES, diagram nodes/relationships, labels) does this extraction "
"convey? On data-rich pages, missing the actual numbers/data points must lower this heavily.\n"
"   - unsupported (0-100): what fraction of THIS extraction's substantive claims CONTRADICT the "
"ground truth or assert specific facts/numbers that are clearly WRONG or invented? Do NOT penalize a "
"longer or more detailed description of the same content (a fuller account of a photo, chart, or "
"diagram) as long as it is CONSISTENT with the page — only genuine errors count. 0 if nothing it says "
"conflicts with the page.\n"
"Grade strictly and differentiate the parsers. An extraction that is empty or near-empty gets "
"info_recall near 0."
)


def schema(letters):
    props = {L: {"type": "object", "additionalProperties": False,
                 "properties": {"info_recall": {"type": "integer"},
                                "unsupported": {"type": "integer"}},
                 "required": ["info_recall", "unsupported"]} for L in letters}
    return {"type": "object", "additionalProperties": False,
            "properties": {
                "page_info_weight": {"type": "integer"},
                "scores": {"type": "object", "additionalProperties": False,
                           "properties": props, "required": list(letters)},
            }, "required": ["page_info_weight", "scores"]}


_local = threading.local()
def client():
    if not hasattr(_local, "c"): _local.c = OpenAI()
    return _local.c


def judge_page(doc, page, gt_md, vendor_md):
    rnd = random.Random(f"{doc}:{page}")
    order = VENDORS[:]; rnd.shuffle(order)
    letters = LETTERS[:len(order)]
    mapping = dict(zip(letters, order))
    blocks = [PROMPT_HEAD, f"\n===== GROUND TRUTH (page reference) =====\n{(gt_md or '')[:GT_CAP]}"]
    for L in letters:
        blob = (vendor_md[mapping[L]].get((doc, page), "") or "(no extraction)")[:VEND_CAP]
        blocks.append(f"\n===== EXTRACTION {L} =====\n{blob}")
    text = "\n".join(blocks)
    fmt = {"format": {"type": "json_schema", "name": "fair_total", "strict": True,
                      "schema": schema(letters)}}
    last = None
    for attempt in range(4):
        try:
            r = client().responses.create(model=MODEL, reasoning={"effort": "low"},
                                          input=[{"role": "user", "content":
                                                  [{"type": "input_text", "text": text}]}],
                                          text=fmt, max_output_tokens=4000)
            obj = json.loads(r.output_text)
            it, ot = r.usage.input_tokens, r.usage.output_tokens
            cost = (it * PRICE_IN + ot * PRICE_OUT) / 1e6
            scores = {mapping[L]: obj["scores"][L] for L in letters}
            return {"doc": doc, "page": page, "weight": obj["page_info_weight"],
                    "scores": scores, "cost_usd": round(cost, 6)}
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    return {"doc": doc, "page": page, "error": str(last), "scores": {}}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    cache_dir = os.environ.get("FT_CACHE", "ground_truth/fair_total_judge")
    out_path = os.environ.get("FT_OUT", "results/_fair_total_judging.json")
    gt_path = os.environ.get("GT_MD", "results/_gt_markdown.json")
    gt = {(r["doc"], r["page"]): r.get("md", "")
          for r in json.load(open(gt_path))}
    vendor_md = {vd: load_pages(vd) for vd in VENDORS}
    targets = sorted(gt.keys())
    os.makedirs(cache_dir, exist_ok=True)

    def task(dp):
        doc, page = dp
        cp = os.path.join(cache_dir, f"{doc}__p{page:04d}.json")
        if os.path.exists(cp):
            return json.load(open(cp))
        res = judge_page(doc, page, gt[dp], vendor_md)
        json.dump(res, open(cp, "w"))
        return res

    t0 = time.time(); out = []; done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(task, dp) for dp in targets]
        for f in futs:
            out.append(f.result()); done += 1
            if done % 25 == 0:
                c = sum(r.get("cost_usd", 0) for r in out)
                print(f"  {done}/{len(targets)} ({time.time()-t0:.0f}s, ${c:.2f})", flush=True)
    json.dump(out, open(out_path, "w"), indent=2)
    errs = [r for r in out if r.get("error")]
    print(f"judged {len(out)} pages; errors {len(errs)}; cost ${sum(r.get('cost_usd',0) for r in out):.2f}")


if __name__ == "__main__":
    main()
