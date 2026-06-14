#!/usr/bin/env python3
"""STAGE B of the element-level eval: grade every vendor on every GT element, blind.

For each page, a BLIND judge sees the page's fixed GT element inventory (Stage A: id, type, label,
key_facts) and all 8 vendors' full page markdown (shuffled A-H). For EACH element it returns, per
vendor: recall (0-100, how much of that element's key_facts the vendor conveyed, paraphrase credited)
and wrong (0-100, how much of what the vendor says ABOUT that element contradicts/​invents). Because the
element carries a fixed TYPE, we then aggregate recall+fidelity BY ELEMENT TYPE across all 599 pages —
the true "who is good at tables vs charts vs prose vs diagrams" answer, free of page-bucket and
document confounds.

Judge default gpt-5 (set JUDGE=gemini for the cross-family run via score_elements_gemini wrapper).
Input: results/_gt_elements.json (Stage A) + vendor MDs. Output: results/_element_judging.json
"""
import os, sys, json, time, random, threading
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from build_vendor_md import VENDORS, load_pages

if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = _l.split("=", 1)[1].strip()

MODEL = "gpt-5"
PRICE_IN, PRICE_OUT = 1.25, 10.0
LETTERS = "ABCDEFGH"
VEND_CAP = int(os.environ.get("EL_VEND_CAP", "6000"))

PROMPT_HEAD = (
"You are a STRICT, BLIND grader of document-extraction completeness, working ELEMENT BY ELEMENT.\n\n"
"You are given a list of the ground-truth CONTENT ELEMENTS of ONE page (each with an id, a type, a "
"short label, and key_facts = the specific information that element contains). Then you are given "
"several parser extractions of the same page, labeled A, B, C, ... (full page text each).\n\n"
"For EACH element id, grade EACH extraction ONLY on whether it conveys THAT element's key_facts, and "
"CREDIT EQUIVALENT PHRASING as fully correct (a table/chart/diagram described in different-but-correct "
"words with the same numbers and relationships is fully captured). Reward information, not wording.\n"
"  - recall (0-100): what fraction of THIS element's key_facts (its numbers, cells, chart data points, "
"nodes/relationships, or prose gist) does this extraction convey? If the extraction does not contain "
"this element at all, recall = 0. On data elements, missing the actual values must lower recall heavily.\n"
"  - wrong (0-100): of what this extraction states ABOUT THIS element, how much CONTRADICTS the key_facts "
"or is clearly invented (wrong numbers/labels)? A fuller-but-consistent description is NOT wrong (0). "
"Only genuine errors count.\n\n"
"Return one entry per element id, with a recall+wrong for every extraction letter. Grade strictly and "
"differentiate the parsers."
)


def schema(ids, letters):
    vend_props = {L: {"type": "object", "additionalProperties": False,
                      "properties": {"recall": {"type": "integer"}, "wrong": {"type": "integer"}},
                      "required": ["recall", "wrong"]} for L in letters}
    item = {"type": "object", "additionalProperties": False,
            "properties": {"id": {"type": "string", "enum": ids},
                           "vendors": {"type": "object", "additionalProperties": False,
                                       "properties": vend_props, "required": list(letters)}},
            "required": ["id", "vendors"]}
    return {"type": "object", "additionalProperties": False,
            "properties": {"elements": {"type": "array", "items": item}},
            "required": ["elements"]}


_local = threading.local()
def client():
    if not hasattr(_local, "c"): _local.c = OpenAI()
    return _local.c


def judge_page(doc, page, elements, vendor_md):
    if not elements:
        return {"doc": doc, "page": page, "scores": [], "cost_usd": 0.0}
    rnd = random.Random(f"{doc}:{page}")
    order = VENDORS[:]; rnd.shuffle(order)
    letters = LETTERS[:len(order)]
    mapping = dict(zip(letters, order))
    el_lines = [f"[{e['id']}] type={e['type']} | {e['label']} | key_facts: {e['key_facts']}"
                for e in elements]
    blocks = [PROMPT_HEAD, "\n===== GROUND-TRUTH ELEMENTS OF THIS PAGE =====\n" + "\n".join(el_lines)]
    for L in letters:
        blob = (vendor_md[mapping[L]].get((doc, page), "") or "(no extraction)")[:VEND_CAP]
        blocks.append(f"\n===== EXTRACTION {L} =====\n{blob}")
    text = "\n".join(blocks)
    ids = [e["id"] for e in elements]
    fmt = {"format": {"type": "json_schema", "name": "elem_scores", "strict": True,
                      "schema": schema(ids, letters)}}
    last = None
    for attempt in range(4):
        try:
            r = client().responses.create(model=MODEL, reasoning={"effort": "low"},
                                          input=[{"role": "user", "content":
                                                  [{"type": "input_text", "text": text}]}],
                                          text=fmt, max_output_tokens=8000)
            obj = json.loads(r.output_text)
            # remap shuffled letters -> vendor names per element
            scores = []
            for ent in obj["elements"]:
                vd = {mapping[L]: ent["vendors"][L] for L in letters if L in ent["vendors"]}
                scores.append({"id": ent["id"], "vendors": vd})
            it, ot = r.usage.input_tokens, r.usage.output_tokens
            cost = (it * PRICE_IN + ot * PRICE_OUT) / 1e6
            return {"doc": doc, "page": page, "scores": scores, "cost_usd": round(cost, 6)}
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    return {"doc": doc, "page": page, "scores": [], "error": str(last)}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    cache_dir = os.environ.get("EL_CACHE", "ground_truth/element_judge")
    out_path = os.environ.get("EL_OUT", "results/_element_judging.json")
    elems = {(r["doc"], r["page"]): r.get("elements", [])
             for r in json.load(open("results/_gt_elements.json"))}
    vendor_md = {vd: load_pages(vd) for vd in VENDORS}
    targets = sorted(elems.keys())
    os.makedirs(cache_dir, exist_ok=True)

    def task(dp):
        doc, page = dp
        cp = os.path.join(cache_dir, f"{doc}__p{page:04d}.json")
        if os.path.exists(cp):
            return json.load(open(cp))
        res = judge_page(doc, page, elems[dp], vendor_md)
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
    print(f"judged {len(out)} pages; errors {len(errs)}; "
          f"cost ${sum(r.get('cost_usd',0) for r in out):.2f}")


if __name__ == "__main__":
    main()
