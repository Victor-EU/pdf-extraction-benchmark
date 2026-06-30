#!/usr/bin/env python3
"""Run Pulse (runpulse.com) in its MOST ADVANCED config (pulse-ultra-2 + refine{tables,text,
formatting} + figure_processing.description; see pulse_common.py) over the full corpus and cache
the per-page response.

Input arm is the per-page PNG render — identical to every other vision vendor here (gpt-5 image,
Gemini, Landing AI, Mistral OCR 4). On this corpus the PNG arm is the settled choice (cf. the
Mistral PNG-vs-PDF A/B and the Landing-AI DPT-2 input A/B, both of which landed on PNG), and per-page
keeps page attribution clean for the category/figure metrics.

Output: ground_truth/pulse/raw/{doc}__p{page:04d}.json   (full /extract response per page; resumable)
Usage:  python3 scripts/pulse_run.py            # ~40-60s/page; few workers (ultra is slow + rate-limits)
        PULSE_WORKERS=4 python3 scripts/pulse_run.py
"""
import os, sys, time, json, threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pulse_common as P

RENDER = "ground_truth/render_full"
RAW = "ground_truth/pulse/raw"
WORKERS = int(os.environ.get("PULSE_WORKERS", "4"))


def main():
    os.makedirs(RAW, exist_ok=True)
    rows = json.load(open(os.path.join(RENDER, "_manifest.json")))
    todo = [m for m in rows
            if not os.path.exists(os.path.join(RAW, f"{m['doc']}__p{m['page']:04d}.json"))]
    print(f"Pulse ({P.MODEL} + refine, {WORKERS} workers) over {len(rows)} pages "
          f"({len(todo)} to do) -> {RAW}")
    t0 = time.time(); lock = threading.Lock(); state = {"done": 0, "err": 0}

    def work(m):
        doc, page = m["doc"], m["page"]
        cp = os.path.join(RAW, f"{doc}__p{page:04d}.json")
        png = os.path.join(RENDER, m["png"])
        try:
            resp, wall = P.extract_call(png)
            resp["_wall"] = round(wall, 2)
            json.dump(resp, open(cp, "w"))
        except Exception as e:
            with lock:
                state["err"] += 1
            print(f"  [err] {doc} p{page}: {e}", file=sys.stderr)
        with lock:
            state["done"] += 1
            if state["done"] % 10 == 0 or state["done"] == len(todo):
                print(f"  {state['done']}/{len(todo)} done ({time.time()-t0:.0f}s, "
                      f"{state['err']} err)", flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(work, todo))
    print(f"done {len(todo)} pages in {time.time()-t0:.0f}s; errors {state['err']} -> {RAW}")


if __name__ == "__main__":
    main()
