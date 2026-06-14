#!/usr/bin/env python3
"""gpt-5 FULL-EXTRACTION harness (distinct from the classifier openai_parser.py).

Re-runs gpt-5 over every page asking it to RECONSTRUCT the page's full information as an
ordered list of blocks, covering the four+graph extraction dimensions:
  1. text   - verbatim prose/headings/marginalia
  2. table  - rendered as GitHub-markdown tables (cells preserved, not flattened)
  3. figures - typed graph|diagram|photo|logo, each with a description; and for GRAPHS the
               recovered DATA (chart type, title, axes+scale, series, per-point values, trend)
  4. spatial - each block carries reading-order (array order) + a coarse position tag

Two input methods (image = rendered PNG; file = native 1-page PDF), same prompt/schema, so the
comparison isolates input method. Resumable per-page cache, threaded.
Output: results/_openai_<mode>_extract.json  +  ground_truth/openai_<mode>_extract/raw/.
"""
import os, sys, json, time, base64, glob, threading
from concurrent.futures import ThreadPoolExecutor
import fitz
from openai import OpenAI

if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = _l.split("=", 1)[1].strip()

MODEL = "gpt-5"
PRICE_IN, PRICE_OUT = 1.25, 10.0

PROMPT = (
"You are a document-parsing engine. RECONSTRUCT the FULL information content of this ONE PDF page "
"as an ordered list of blocks, in natural READING ORDER. Capture EVERYTHING on the page — miss nothing.\n\n"
"For each block set:\n"
"- type: text | heading | table | figure | marginalia | other\n"
"- position: coarse location on the page (top-left … bottom-right, or full-page)\n"
"- figure_kind: for figures only, one of graph|diagram|photo|logo (else 'none')\n"
"- content: see rules below\n\n"
"CONTENT RULES:\n"
"• text/heading/marginalia: transcribe the text VERBATIM (keep numbers, units, punctuation exactly). "
"Do not summarize.\n"
"• table: render as a GitHub-markdown table with EVERY row and cell, headers included. Preserve all "
"numbers exactly. Do not flatten a table into prose.\n"
"• figure = graph/chart (line/bar/pie/scatter/area/waterfall): RECOVER THE DATA, not just a label. In "
"content give: chart type; title; x-axis and y-axis labels WITH their scale/tick values; each series "
"name; the per-point DATA VALUES (read/estimate them from the plot, mark estimates with ~); and the "
"overall trend. Finance pages depend on these numbers — extract them.\n"
"• figure = diagram (flow/process/cycle/org-chart/value-chain/network): describe the structure — the "
"components/nodes, their labels, and the relationships/flow between them.\n"
"• figure = photo/logo: one short factual description (what it shows / whose logo).\n\n"
"Return only the blocks. Be exhaustive and faithful; never invent content that is not on the page."
)

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "blocks": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "type": {"type": "string",
                             "enum": ["text", "heading", "table", "figure", "marginalia", "other"]},
                    "position": {"type": "string",
                                 "enum": ["top-left", "top-center", "top-right", "mid-left", "center",
                                          "mid-right", "bottom-left", "bottom-center", "bottom-right",
                                          "full-page"]},
                    "figure_kind": {"type": "string",
                                    "enum": ["none", "graph", "diagram", "photo", "logo"]},
                    "content": {"type": "string"},
                },
                "required": ["type", "position", "figure_kind", "content"],
            },
        },
    },
    "required": ["blocks"],
}
FMT = {"format": {"type": "json_schema", "name": "page_extraction", "strict": True, "schema": SCHEMA}}

_local = threading.local()
def get_client():
    if not hasattr(_local, "client"):
        _local.client = OpenAI()
    return _local.client

_docs = {}
_docs_lock = threading.Lock()
def page_pdf_b64(pdf_path, page0):
    with _docs_lock:
        if pdf_path not in _docs:
            _docs[pdf_path] = fitz.open(pdf_path)
        one = fitz.open()
        one.insert_pdf(_docs[pdf_path], from_page=page0, to_page=page0)
        b = one.tobytes(); one.close()
    return base64.b64encode(b).decode()


def call(mode, png_path, pdf_path, page0):
    client = get_client()
    if mode == "image":
        b64 = base64.b64encode(open(png_path, "rb").read()).decode()
        content = [{"type": "input_text", "text": PROMPT},
                   {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"}]
    else:
        pb64 = page_pdf_b64(pdf_path, page0)
        content = [{"type": "input_text", "text": PROMPT},
                   {"type": "input_file", "filename": "page.pdf",
                    "file_data": f"data:application/pdf;base64,{pb64}"}]
    t0 = time.perf_counter()
    last = None
    for attempt in range(4):
        try:
            r = client.responses.create(model=MODEL, reasoning={"effort": "low"},
                                        input=[{"role": "user", "content": content}],
                                        text=FMT, max_output_tokens=16000)
            dt = time.perf_counter() - t0
            obj = json.loads(r.output_text)
            it, ot = r.usage.input_tokens, r.usage.output_tokens
            cost = (it * PRICE_IN + ot * PRICE_OUT) / 1e6
            return {"blocks": obj.get("blocks", []), "seconds": round(dt, 2),
                    "in_tok": it, "out_tok": ot, "cost_usd": round(cost, 6),
                    "status": getattr(r, "status", None)}
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    return {"blocks": [], "error": str(last), "seconds": 0.0,
            "in_tok": 0, "out_tok": 0, "cost_usd": 0.0}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "image"
    assert mode in ("image", "file")
    render = "ground_truth/render_full"
    cache_dir = f"ground_truth/openai_{mode}_extract/raw"
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs("results", exist_ok=True)
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    manifest = json.load(open(os.path.join(render, "_manifest.json")))
    pdfs = {os.path.splitext(os.path.basename(p))[0]: p for p in glob.glob("Data/*.pdf")}

    def task(m):
        doc, page = m["doc"], m["page"]
        cpath = os.path.join(cache_dir, f"{doc}__p{page:04d}.json")
        if os.path.exists(cpath):
            return json.load(open(cpath))
        res = call(mode, os.path.join(render, m["png"]), pdfs[doc], page - 1)
        res["doc"], res["page"] = doc, page
        json.dump(res, open(cpath, "w"), indent=2)
        return res

    t0 = time.time(); results = [None] * len(manifest); done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(task, m): i for i, m in enumerate(manifest)}
        for fut in list(futs):
            results[futs[fut]] = fut.result()
            done += 1
            if done % 25 == 0:
                cost = sum(r.get("cost_usd", 0) for r in results if r)
                print(f"  {done}/{len(manifest)} ({time.time()-t0:.0f}s, ${cost:.2f})", flush=True)

    results.sort(key=lambda r: (r["doc"], r["page"]))
    json.dump(results, open(f"results/_openai_{mode}_extract.json", "w"), indent=2)
    errs = [r for r in results if r.get("error")]
    tot = sum(r.get("cost_usd", 0) for r in results)
    secs = [r["seconds"] for r in results if r.get("seconds")]
    trunc = [r for r in results if r.get("status") == "incomplete"]
    print(f"\nEXTRACT mode={mode}: {len(results)} pages in {time.time()-t0:.0f}s ({workers} workers); "
          f"mean {sum(secs)/len(secs):.2f}s/pg; cost ${tot:.2f}; errors {len(errs)}; truncated {len(trunc)}")


if __name__ == "__main__":
    main()
