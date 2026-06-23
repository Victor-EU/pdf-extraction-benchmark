#!/usr/bin/env python3
"""Run Mistral OCR-4 (advanced config: mistral-ocr-4-0 + table_format=html + per-image bbox
annotation) over the corpus and cache the full per-page response.

Input arm is chosen by the PNG-vs-PDF A/B (ab_mistral_input.py + ab_score_mistral_input.py) and
set via MISTRAL_INPUT (png|pdf); both arms reduce identically downstream so only input fidelity
differs. Like the other vision vendors, OCR-4's natural per-page unit is one rendered page (PNG)
or one born-digital page (PDF) — never the whole doc — so attribution stays clean.

Output: ground_truth/mistral/raw/{doc}__p{page:04d}.json   (full OCR response per page; resumable)
Usage:  MISTRAL_INPUT=png ./.venv-mistral/bin/python scripts/mistral_run.py
"""
import os, sys, time, json, threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mistral_common as M
from corpus import discover_pdfs

RENDER = "ground_truth/render_full"
RAW = "ground_truth/mistral/raw"
ARM = os.environ.get("MISTRAL_INPUT", "png")
WORKERS = int(os.environ.get("MISTRAL_WORKERS", "8"))


def pdfs():
    return discover_pdfs()  # case-insensitive *.pdf/*.PDF discovery (corpus.py)


def main():
    os.makedirs(RAW, exist_ok=True)
    cl = M.client()                      # mistralai client is thread-safe (httpx under the hood)
    P = pdfs()
    rows = json.load(open(os.path.join(RENDER, "_manifest.json")))
    todo = [m for m in rows
            if not os.path.exists(os.path.join(RAW, f"{m['doc']}__p{m['page']:04d}.json"))]
    print(f"OCR-4 ({M.MODEL}, input={ARM}, {WORKERS} workers) "
          f"over {len(rows)} pages ({len(todo)} to do) -> {RAW}")
    t0 = time.time(); lock = threading.Lock(); state = {"done": 0, "err": 0}

    def work(m):
        doc, page = m["doc"], m["page"]
        cp = os.path.join(RAW, f"{doc}__p{page:04d}.json")
        if ARM == "pdf":
            document = {"type": "document_url", "document_url": M.page_pdf_datauri(P[doc], page)}
        else:
            png = os.path.join(RENDER, f"{doc}__p{page:04d}.png")
            document = {"type": "image_url", "image_url": M.png_datauri(png)}
        try:
            resp, wall = M.ocr_call(cl, document)
            resp["_wall"] = round(wall, 2)
            json.dump(resp, open(cp, "w"))
        except Exception as e:
            with lock:
                state["err"] += 1
            print(f"  [err] {doc} p{page}: {e}", file=sys.stderr)
        with lock:
            state["done"] += 1
            if state["done"] % 25 == 0:
                print(f"  {state['done']}/{len(todo)} ({time.time()-t0:.0f}s, {state['err']} err)",
                      flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(work, todo))
    print(f"done {len(todo)} pages in {time.time()-t0:.0f}s; errors {state['err']} -> {RAW}")


if __name__ == "__main__":
    main()
