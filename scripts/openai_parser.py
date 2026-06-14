#!/usr/bin/env python3
"""OpenAI page classifier — a candidate parsing solution (TWO input methods).

OpenAI has no dedicated document-parsing service; "parsing" = feeding the page to
a vision-capable LLM. We evaluate BOTH ways of handing a page to gpt-5, holding the
model / prompt / schema constant so the comparison isolates the INPUT METHOD:

  mode=image : send our rendered PNG of the page          (LLM vision on a raster)
  mode=file  : send the single-page PDF; OpenAI itself     (native PDF ingestion:
               extracts the text layer + a page image       born-digital text + image)

Structured Outputs force exactly one of the 6 categories. Resumable (per-page raw
cache), threaded. Output: results/_openai_<mode>_solution.json [{doc,page,label,seconds,cost_usd}].
"""
import os, sys, json, time, base64, glob, threading
from concurrent.futures import ThreadPoolExecutor
import fitz
from openai import OpenAI

# load OPENAI_API_KEY from gitignored .env
if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = _l.split("=", 1)[1].strip()

MODEL = "gpt-5"
# gpt-5 API pricing (USD per 1M tokens)
PRICE_IN, PRICE_OUT = 1.25, 10.0
CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]

PROMPT = (
"You are classifying ONE page of a PDF into exactly ONE category for a parsing benchmark. "
"Pick the DOMINANT content type a parser would most need to handle.\n\n"
"Categories:\n"
"1. Text - prose/paragraphs dominate (INCLUDES sparse whitespace-heavy text: bios, contact, "
"assurance letters). If the real content is textual, it's Text even when not visually dense.\n"
"2. Table - rows x columns / matrix data dominate (INCLUDES financial statements, comparison & "
"risk matrices, glossaries, logo-rich matrices where logos are cell content).\n"
"3. Chart/Diagram - data viz AND schematics: bar/line/pie/plots; flow/process/cycle/network/"
"value-chain diagrams; timelines/roadmaps; and KPI/icon infographics (icon+big-number dashboards).\n"
"4. Mixed - NO single dominant type; 2+ substantial types coexist (~<60% each). Use only when you "
"genuinely cannot pick a dominant type, NOT as a default.\n"
"5. Cover/Divider - BY FUNCTION: title pages, section-break/divider pages, back covers - EVEN when a "
"decorative photo/illustration fills the page. Function beats appearance.\n"
"6. Image/Photo - TRUE photographic content as the page's substance: a full-page content photo or a "
"photo gallery/grid that IS the point. NOT covers/dividers. Small, rare category.\n\n"
"Warnings: whitespace-heavy text pages are NOT dividers; charts with gridlines are NOT tables; logos "
"in a matrix are Table cell content; a decorative photo on a title/section page is Cover/Divider.\n"
"Set confidence low when two categories are genuinely close."
)

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "label": {"type": "string", "enum": CATS},
        "confidence": {"type": "string", "enum": ["high", "med", "low"]},
        "rationale": {"type": "string"},
    },
    "required": ["label", "confidence", "rationale"],
}
FMT = {"format": {"type": "json_schema", "name": "page_label", "strict": True, "schema": SCHEMA}}

_local = threading.local()
def get_client():
    if not hasattr(_local, "client"):
        _local.client = OpenAI()
    return _local.client

_docs = {}
_docs_lock = threading.Lock()
def page_pdf_b64(pdf_path, page0):
    """Extract a single page as its own 1-page PDF, base64."""
    with _docs_lock:
        if pdf_path not in _docs:
            _docs[pdf_path] = fitz.open(pdf_path)
        src = _docs[pdf_path]
        one = fitz.open()
        one.insert_pdf(src, from_page=page0, to_page=page0)
        b = one.tobytes()
        one.close()
    return base64.b64encode(b).decode()


def call(mode, png_path, pdf_path, page0):
    client = get_client()
    if mode == "image":
        b64 = base64.b64encode(open(png_path, "rb").read()).decode()
        content = [{"type": "input_text", "text": PROMPT},
                   {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"}]
    else:  # file
        pb64 = page_pdf_b64(pdf_path, page0)
        content = [{"type": "input_text", "text": PROMPT},
                   {"type": "input_file", "filename": "page.pdf",
                    "file_data": f"data:application/pdf;base64,{pb64}"}]
    t0 = time.perf_counter()
    last = None
    for attempt in range(4):
        try:
            r = client.responses.create(model=MODEL, reasoning={"effort": "low"},
                                        input=[{"role": "user", "content": content}], text=FMT)
            dt = time.perf_counter() - t0
            obj = json.loads(r.output_text)
            it, ot = r.usage.input_tokens, r.usage.output_tokens
            cost = (it * PRICE_IN + ot * PRICE_OUT) / 1e6
            obj.update(seconds=round(dt, 2), in_tok=it, out_tok=ot, cost_usd=round(cost, 6))
            return obj
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    return {"label": "Text", "confidence": "low", "rationale": "ERROR",
            "error": str(last), "seconds": 0.0, "in_tok": 0, "out_tok": 0, "cost_usd": 0.0}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "image"
    assert mode in ("image", "file")
    render = "ground_truth/render_full"
    cache_dir = f"ground_truth/openai_{mode}/raw"
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

    t0 = time.time()
    results = [None] * len(manifest)
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(task, m): i for i, m in enumerate(manifest)}
        for fut in list(futs):
            i = futs[fut]
            results[i] = fut.result()
            done += 1
            if done % 25 == 0:
                print(f"  {done}/{len(manifest)} ({time.time()-t0:.0f}s)", flush=True)

    results.sort(key=lambda r: (r["doc"], r["page"]))
    sol = [{"doc": r["doc"], "page": r["page"], "label": r["label"],
            "seconds": r.get("seconds", 0.0), "cost_usd": r.get("cost_usd", 0.0)} for r in results]
    out = f"results/_openai_{mode}_solution.json"
    json.dump(sol, open(out, "w"), indent=2)
    json.dump(results, open(f"results/_openai_{mode}_full.json", "w"), indent=2)
    errs = [r for r in results if r.get("error")]
    tot_cost = sum(r.get("cost_usd", 0) for r in results)
    secs = [r["seconds"] for r in results if r.get("seconds")]
    print(f"\nmode={mode}: {len(results)} pages in {time.time()-t0:.0f}s wall ({workers} workers); "
          f"per-page mean {sum(secs)/len(secs):.2f}s; total cost ${tot_cost:.2f}; errors {len(errs)}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
