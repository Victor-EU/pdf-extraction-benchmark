#!/usr/bin/env python3
"""CONTROLLED audit re-judge: does the fair-total metric over-credit STRUCTURE loss?

Hypothesis (industry-expert challenge): PyMuPDF extracts the right characters/numbers but
LOSES STRUCTURE (table grouping, reading order, diagram relationships). The canonical
fair-total judge rewards information PRESENCE with paraphrase tolerance, so it may credit a
scrambled-but-complete token dump as high recall.

This script re-judges the SAME pages with the SAME vendors, same blind shuffle, same caps —
the ONLY change is the rubric: a table/chart/diagram counts as captured ONLY IF the
RELATIONSHIPS / BINDINGS / READING ORDER are preserved well enough to recover which value
belongs to which row/column/node. A flat list of correct tokens whose groupings are
destroyed scores LOW. Paraphrase tolerance is KEPT (correct structure stated in words = full
credit), so this is not a verbosity or format penalty — it is a structure-fidelity test.

Target set: the relational-DIAGRAM pages (figure-GT diagrams[] non-empty) + a flag to add the
multi-table pages. Output to its own cache/JSON so canonical files are untouched. Compare
each vendor's strict score to its canonical fair-total info_recall on the SAME pages: the
DELTA per vendor is the result. If PyMuPDF's delta is large and negative while structure-aware
vendors (Gemini/Landing AI/gpt-5) barely move, the inflation is a metric choice, confirmed.
"""
import os, sys, json, time, random, threading
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI

sys.path.insert(0, "scripts")
from build_vendor_md import VENDORS, load_pages

if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = _l.split("=", 1)[1].strip()

MODEL = "gpt-5"
PRICE_IN, PRICE_OUT = 1.25, 10.0
LETTERS = "ABCDEFGHIJKL"
GT_CAP = int(os.environ.get("FT_GT_CAP", "16000"))
VEND_CAP = int(os.environ.get("FT_VEND_CAP", "16000"))

# Structure-strict rubric. Same task shell as score_fair_total.py, but info_recall is
# redefined to require that relationships/bindings/order survive, not just token presence.
PROMPT_HEAD = (
"You are a STRICT, BLIND grader of document-extraction STRUCTURAL FIDELITY. Below is a "
"GROUND-TRUTH transcription of ONE page, then several parser extractions of the same page, "
"labeled A, B, C, ...\n\n"
"The GROUND TRUTH lists the page's real information AND its structure: table rows/columns, "
"chart series and their data points, and diagram nodes WITH their relationships (who reports "
"to whom, which value belongs to which node/row/column).\n\n"
"TASK:\n"
"1) page_info_weight (1-10): how much substantive STRUCTURED information does this page hold? "
"1 = nearly empty; 10 = very dense (large multi-column table, multi-series chart, or detailed "
"org/process diagram with many bindings).\n"
"2) For EACH extraction, grade ONLY against the ground truth, crediting EQUIVALENT PHRASING: a "
"table/chart/diagram described in DIFFERENT WORDS that conveys the same facts AND THE SAME "
"STRUCTURE (same row-to-value, column-to-value, node-to-relationship bindings) is fully "
"captured. A correct STRUCTURE stated in prose gets full credit — this is NOT a formatting or "
"verbosity test.\n"
"   - info_recall (0-100): what fraction of the ground truth's STRUCTURED information does this "
"extraction actually convey — such that a reader could RECOVER which value belongs to which "
"row/column, which data point belongs to which series, and which node relates to which? "
"CRITICAL: tokens present but with their bindings DESTROYED do NOT count. If an extraction "
"lists all the right labels and numbers but in a scrambled or flattened order so that the "
"reader CANNOT reliably tell which number goes with which row/node, or merges several distinct "
"tables/sections into one indistinguishable run, or drops the reporting hierarchy of a diagram, "
"score it LOW (typically 20-50) even though the raw tokens are all there. Reward RECOVERABLE "
"STRUCTURE, not token presence.\n"
"   - unsupported (0-100): what fraction of THIS extraction's substantive claims CONTRADICT the "
"ground truth or assert specific facts/numbers that are clearly WRONG or invented? Do NOT "
"penalize a longer but consistent description. 0 if nothing conflicts.\n"
"Grade strictly and differentiate the parsers. An extraction that is empty or near-empty gets "
"info_recall near 0."
)


def schema(letters):
    props = {L: {"type": "object", "additionalProperties": False,
                 "properties": {"info_recall": {"type": "integer"},
                                "unsupported": {"type": "integer"}},
                 "required": ["info_recall", "unsupported"]} for L in letters}
    return {"type": "object", "additionalProperties": False,
            "properties": {"page_info_weight": {"type": "integer"},
                           "scores": {"type": "object", "additionalProperties": False,
                                      "properties": props, "required": list(letters)}},
            "required": ["page_info_weight", "scores"]}


_local = threading.local()
def client():
    if not hasattr(_local, "c"):
        _local.c = OpenAI()
    return _local.c


def judge_page(doc, page, gt_md, vendor_md):
    rnd = random.Random(f"{doc}:{page}")          # SAME seed as canonical -> same shuffle
    order = VENDORS[:]; rnd.shuffle(order)
    letters = LETTERS[:len(order)]
    mapping = dict(zip(letters, order))
    blocks = [PROMPT_HEAD, f"\n===== GROUND TRUTH (page reference) =====\n{(gt_md or '')[:GT_CAP]}"]
    for L in letters:
        blob = (vendor_md[mapping[L]].get((doc, page), "") or "(no extraction)")[:VEND_CAP]
        blocks.append(f"\n===== EXTRACTION {L} =====\n{blob}")
    text = "\n".join(blocks)
    fmt = {"format": {"type": "json_schema", "name": "structure_strict", "strict": True,
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
    cache_dir = os.environ.get("SS_CACHE", "ground_truth/structure_strict_judge")
    out_path = os.environ.get("SS_OUT", "results/_structure_strict_judging.json")
    gt_path = os.environ.get("GT_MD", "results/_gt_markdown.json")

    # target set: relational-diagram pages (figure-GT diagrams[] non-empty)
    fj = json.load(open("results/_figure_judging.json"))
    targets = sorted({(r["doc"], r["page"]) for r in fj if r.get("diagrams")})
    if os.environ.get("SS_ADD_MULTITABLE"):
        cat = {(e["doc"], e["page"]): e["final_label"]
               for e in json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))["pages"]}
        targets = sorted(set(targets) | {k for k, v in cat.items() if v == "Table"})

    gt = {(r["doc"], r["page"]): r.get("md", "") for r in json.load(open(gt_path))}
    vendor_md = {vd: load_pages(vd) for vd in VENDORS}
    os.makedirs(cache_dir, exist_ok=True)
    print(f"structure-strict re-judge on {len(targets)} pages, {len(VENDORS)} vendors")

    def task(dp):
        doc, page = dp
        cp = os.path.join(cache_dir, f"{doc}__p{page:04d}.json")
        if os.path.exists(cp):
            return json.load(open(cp))
        res = judge_page(doc, page, gt.get(dp, ""), vendor_md)
        json.dump(res, open(cp, "w"))
        return res

    t0 = time.time(); out = []; done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(task, dp) for dp in targets]
        for f in futs:
            out.append(f.result()); done += 1
            if done % 20 == 0:
                c = sum(r.get("cost_usd", 0) for r in out)
                print(f"  {done}/{len(targets)} ({time.time()-t0:.0f}s, ${c:.2f})", flush=True)
    json.dump(out, open(out_path, "w"), indent=2)
    errs = [r for r in out if r.get("error")]
    print(f"judged {len(out)} pages; errors {len(errs)}; "
          f"cost ${sum(r.get('cost_usd',0) for r in out):.2f}")


if __name__ == "__main__":
    main()
