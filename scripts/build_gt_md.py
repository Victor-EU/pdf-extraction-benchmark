#!/usr/bin/env python3
"""Build the GROUND-TRUTH markdown — a complete, faithful, reading-order transcription of all
599 pages, used as the reference for the document-level "fair total" information comparison.

Built with gpt-5 vision at effort=medium and a FREE-FORM markdown transcription task (deliberately
a different task + format than the block-JSON extraction we score, so it's a reference document,
not a vendor's scored output). gpt-5 is NOT graded fairly against this (its own family) — its
fair-total cell is reported as a reference/upper-bound, not a comparable score. The vendor under
scrutiny (Landing AI) and the others are graded cleanly.

Per-page cache: ground_truth/gt_markdown/raw/<doc>__pNNNN.md  (resumable)
Consolidated:   ground_truth/GROUND_TRUTH.md  (599 pages, in order)
Usage: python3 scripts/build_gt_md.py [workers]
"""
import os, sys, json, time, base64, glob, threading
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI

if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = _l.split("=", 1)[1].strip()

MODEL = "gpt-5"
PRICE_IN, PRICE_OUT = 1.25, 10.0
RENDER = "ground_truth/render_full"
CACHE = "ground_truth/gt_markdown/raw"

PROMPT = (
"You are a meticulous document transcriber. Produce a COMPLETE, FAITHFUL Markdown transcription of "
"this ONE page, in natural reading order. This is a GROUND-TRUTH reference document, so miss NOTHING "
"and invent NOTHING.\n\n"
"Rules:\n"
"- Transcribe ALL text (headings, prose, bullets, captions, marginalia, footnotes, page numbers) "
"VERBATIM — keep numbers, units, and punctuation exactly.\n"
"- Render EVERY table as a GitHub-markdown table with all rows, cells and headers; preserve every "
"number exactly. Never flatten a table into prose.\n"
"- For EVERY chart/graph (line/bar/pie/scatter/area/waterfall) write a line starting `**Chart:**` "
"giving the chart type, title, x/y axis labels WITH their scale or tick values, each series name, "
"the per-point DATA VALUES (read them off the plot; prefix estimates with ~), and the trend.\n"
"- For EVERY diagram (flow/process/cycle/org-chart/value-chain/network) write a line starting "
"`**Diagram:**` describing the nodes/components, their labels, and the relationships/flow.\n"
"- For photos/logos write `**Image:**` / `**Logo:**` with a short factual description.\n\n"
"Output ONLY the Markdown transcription of the page — no preamble, no commentary."
)

_local = threading.local()
def client():
    if not hasattr(_local, "c"): _local.c = OpenAI()
    return _local.c


def transcribe(png_path):
    b64 = base64.b64encode(open(png_path, "rb").read()).decode()
    content = [{"type": "input_text", "text": PROMPT},
               {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"}]
    last = None
    for attempt in range(4):
        try:
            t0 = time.perf_counter()
            r = client().responses.create(model=MODEL, reasoning={"effort": "medium"},
                                          input=[{"role": "user", "content": content}],
                                          max_output_tokens=16000)
            it, ot = r.usage.input_tokens, r.usage.output_tokens
            return {"md": r.output_text or "", "in_tok": it, "out_tok": ot,
                    "cost_usd": round((it * PRICE_IN + ot * PRICE_OUT) / 1e6, 6),
                    "seconds": round(time.perf_counter() - t0, 2),
                    "status": getattr(r, "status", None)}
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    return {"md": "", "error": str(last), "in_tok": 0, "out_tok": 0, "cost_usd": 0.0, "seconds": 0.0}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    os.makedirs(CACHE, exist_ok=True)
    manifest = json.load(open(os.path.join(RENDER, "_manifest.json")))

    def task(m):
        doc, page = m["doc"], m["page"]
        cp = os.path.join(CACHE, f"{doc}__p{page:04d}.json")
        if os.path.exists(cp):
            return json.load(open(cp))
        res = transcribe(os.path.join(RENDER, m["png"]))
        res["doc"], res["page"] = doc, page
        json.dump(res, open(cp, "w"))
        return res

    t0 = time.time(); results = [None] * len(manifest); done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(task, m): i for i, m in enumerate(manifest)}
        for fut in list(futs):
            results[futs[fut]] = fut.result(); done += 1
            if done % 25 == 0:
                c = sum(r.get("cost_usd", 0) for r in results if r)
                print(f"  {done}/{len(manifest)} ({time.time()-t0:.0f}s, ${c:.2f})", flush=True)

    results.sort(key=lambda r: (r["doc"], r["page"]))
    # consolidated readable GT doc
    L = ["# GROUND TRUTH — faithful transcription of all 599 pages (gpt-5 vision, reference)\n"]
    for r in results:
        L.append(f"\n\n---\n\n## {r['doc']} — page {r['page']}\n")
        L.append(r.get("md", "").strip() or "*(empty)*")
    open("ground_truth/GROUND_TRUTH.md", "w").write("\n".join(L) + "\n")
    json.dump(results, open("results/_gt_markdown.json", "w"))
    errs = [r for r in results if r.get("error")]
    trunc = [r for r in results if r.get("status") == "incomplete"]
    tot = sum(r.get("cost_usd", 0) for r in results)
    secs = [r["seconds"] for r in results if r.get("seconds")]
    print(f"\nGT built: {len(results)} pages in {time.time()-t0:.0f}s; mean "
          f"{sum(secs)/len(secs):.2f}s/pg; cost ${tot:.2f}; errors {len(errs)}; truncated {len(trunc)}")
    print("-> ground_truth/GROUND_TRUTH.md  +  results/_gt_markdown.json")


if __name__ == "__main__":
    main()
