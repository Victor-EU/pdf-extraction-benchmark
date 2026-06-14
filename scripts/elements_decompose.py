#!/usr/bin/env python3
"""STAGE A of the element-level eval: decompose each GT page into typed, atomic content elements.

The page-category eval gives ONE label per page, so a page with a heading + table + chart + footnote
is scored as a single bucket — it can't say who's good at tables vs charts vs prose. This stage tags
every section of the canonical v2 GROUND TRUTH into a fixed inventory of typed elements, so Stage B can
score each vendor element-by-element and aggregate BY TYPE across the whole corpus (a chart counts as a
chart whether it sits on a deck slide or an annual-report page — removing the doc/category confound).

Input: results/_gt_markdown.json (v2 canonical GT, text only — authoritative for content).
Output: results/_gt_elements.json — per page: [{id,type,label,key_facts,salience}].
"""
import os, sys, json, time, threading
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI

if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = _l.split("=", 1)[1].strip()

MODEL = "gpt-5"
PRICE_IN, PRICE_OUT = 1.25, 10.0
GT_CAP = 9000
TYPES = ["title_heading", "narrative_text", "data_table", "chart", "diagram",
         "kpi_callout", "footnote_source"]

PROMPT = (
"You decompose ONE page of a document (given as a faithful ground-truth transcription) into its "
"distinct CONTENT ELEMENTS, so each can later be graded independently. A single page usually holds "
"SEVERAL elements (e.g. a title, a paragraph, a data table, a chart, a footnote) — separate them.\n\n"
"For each element output:\n"
"- type, exactly one of: "
"  title_heading (page/section/slide titles & headers);"
"  narrative_text (prose paragraphs and bulleted body/feature text);"
"  data_table (a grid of rows×columns of values/labels);"
"  chart (a graph plotting DATA: bar/line/pie/donut/area/scatter/combo, with axes or data series);"
"  diagram (structure WITHOUT data series: flow/process, org chart, map, timeline, schematic, matrix of boxes);"
"  kpi_callout (a highlighted standalone metric / big-number stat / labelled figure box);"
"  footnote_source (sources, page numbers, confidentiality lines, logos, photo captions, running headers — page chrome).\n"
"- label: a short human name for the element (<8 words).\n"
"- key_facts: the SPECIFIC information that an extraction MUST convey to capture this element — the "
"actual numbers, table cells, chart data points/series, node relationships, or the gist of the prose. "
"Be concrete and include the load-bearing values; this is the answer key for grading. Keep < 600 chars.\n"
"- salience (1-5): how much of the page's real information this element carries "
"(1 = chrome/footnote/logo; 3 = a normal paragraph or small chart; 5 = a dense data table or rich "
"multi-series chart that is the point of the page).\n\n"
"Rules: be EXHAUSTIVE — every distinct piece of content becomes an element, including footnotes/sources/"
"page numbers (as footnote_source). Do NOT merge a chart and its surrounding prose into one element. "
"Do NOT invent content not in the transcription. Order elements top-to-bottom as they appear."
)

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"elements": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "type": {"type": "string", "enum": TYPES},
            "label": {"type": "string"},
            "key_facts": {"type": "string"},
            "salience": {"type": "integer"},
        }, "required": ["type", "label", "key_facts", "salience"]}}},
    "required": ["elements"],
}

_local = threading.local()
def client():
    if not hasattr(_local, "c"): _local.c = OpenAI()
    return _local.c


def decompose(doc, page, gt_md):
    text = PROMPT + f"\n\n===== GROUND TRUTH (page {page}) =====\n{(gt_md or '')[:GT_CAP]}"
    fmt = {"format": {"type": "json_schema", "name": "elements", "strict": True, "schema": SCHEMA}}
    last = None
    for attempt in range(4):
        try:
            r = client().responses.create(model=MODEL, reasoning={"effort": "low"},
                                          input=[{"role": "user", "content":
                                                  [{"type": "input_text", "text": text}]}],
                                          text=fmt, max_output_tokens=5000)
            obj = json.loads(r.output_text)
            els = obj["elements"]
            for i, e in enumerate(els, 1):
                e["id"] = f"e{i}"
            it, ot = r.usage.input_tokens, r.usage.output_tokens
            cost = (it * PRICE_IN + ot * PRICE_OUT) / 1e6
            return {"doc": doc, "page": page, "elements": els, "cost_usd": round(cost, 6)}
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    return {"doc": doc, "page": page, "elements": [], "error": str(last)}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    cache_dir = "ground_truth/gt_elements"
    out_path = "results/_gt_elements.json"
    gt = {(r["doc"], r["page"]): r.get("md", "") for r in json.load(open("results/_gt_markdown.json"))}
    targets = sorted(gt.keys())
    os.makedirs(cache_dir, exist_ok=True)

    def task(dp):
        doc, page = dp
        cp = os.path.join(cache_dir, f"{doc}__p{page:04d}.json")
        if os.path.exists(cp):
            return json.load(open(cp))
        res = decompose(doc, page, gt[dp])
        json.dump(res, open(cp, "w"))
        return res

    t0 = time.time(); out = []; done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(task, dp) for dp in targets]
        for f in futs:
            out.append(f.result()); done += 1
            if done % 25 == 0:
                c = sum(r.get("cost_usd", 0) for r in out)
                ne = sum(len(r.get("elements", [])) for r in out)
                print(f"  {done}/{len(targets)} ({time.time()-t0:.0f}s, ${c:.2f}, {ne} elements)", flush=True)
    json.dump(out, open(out_path, "w"), indent=2)
    errs = [r for r in out if r.get("error")]
    ne = sum(len(r.get("elements", [])) for r in out)
    print(f"decomposed {len(out)} pages → {ne} elements; errors {len(errs)}; "
          f"cost ${sum(r.get('cost_usd',0) for r in out):.2f}")


if __name__ == "__main__":
    main()
