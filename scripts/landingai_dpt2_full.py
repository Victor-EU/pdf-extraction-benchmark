#!/usr/bin/env python3
"""Full-corpus Landing AI DPT-2 pass (NEW v1/ade/parse, model=dpt-2-latest, Bearer auth).

The DPT-2 replacement for the legacy landingai_pass.py. Same per-page PNG input as the legacy
benchmark (render_full) so the re-benchmark is apples-to-apples — only the endpoint+model change
(see ground_truth/landingai_dpt2_ab/RESULTS.md: PNG input beats PDF-page input for DPT-2; the win
is the model). Parallel, resumes from raw on disk.

Usage:  python3 scripts/landingai_dpt2_full.py [workers]
Output: ground_truth/landingai_dpt2_full/raw/<doc>__pXXXX.png.json
"""
import os, sys, json, time, requests
from concurrent.futures import ThreadPoolExecutor, as_completed

PARSE_URL = "https://api.va.landing.ai/v1/ade/parse"
MODEL = "dpt-2-latest"
RENDER = "ground_truth/render_full"
OUT = "ground_truth/landingai_dpt2_full"


def api_key():
    if os.path.exists(".env"):
        for l in open(".env"):
            if l.startswith("VISION_AGENT_API_KEY="):
                v = l.split("=", 1)[1].strip()
                if v:
                    return v
    return os.environ["VISION_AGENT_API_KEY"]


def call_parse(png, key, retries=5):
    headers = {"Authorization": f"Bearer {key}"}
    last = None
    for a in range(retries):
        try:
            with open(png, "rb") as f:
                files = {"document": (os.path.basename(png), f, "image/png")}
                data = {"model": MODEL}
                t0 = time.time()
                r = requests.post(PARSE_URL, headers=headers, files=files, data=data, timeout=180)
            wall = time.time() - t0
            if r.status_code == 200:
                return r.json(), wall, None
            last = f"HTTP {r.status_code}: {r.text[:300]}"
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(min(60, 2 ** a + 1))
                continue
            return None, 0, last
        except Exception as e:
            last = str(e)
            time.sleep(min(60, 2 ** a + 1))
    return None, 0, last


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    key = api_key()
    raw_dir = os.path.join(OUT, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    manifest = json.load(open(os.path.join(RENDER, "_manifest.json")))

    def work(item):
        png_name = item["png"]
        img = os.path.join(RENDER, png_name)
        raw_path = os.path.join(raw_dir, png_name + ".json")
        if os.path.exists(raw_path):
            return dict(doc=item["doc"], page=item["page"], status="cached")
        resp, wall, err = call_parse(img, key)
        if resp is None:
            return dict(doc=item["doc"], page=item["page"], status="ERROR", error=err)
        resp["_wall"] = wall
        json.dump(resp, open(raw_path, "w"))
        credit = (resp.get("metadata", {}) or {}).get("credit_usage")
        return dict(doc=item["doc"], page=item["page"], status="ok",
                    credit=credit, wall=round(wall, 1))

    t0 = time.time(); done = 0; errs = []; credits = 0.0; cached = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(work, it): it for it in manifest}
        for fut in as_completed(futs):
            r = fut.result(); done += 1
            if r["status"] == "ERROR":
                errs.append(r)
            elif r["status"] == "cached":
                cached += 1
            else:
                credits += r.get("credit") or 0
            if done % 25 == 0:
                print(f"  {done}/{len(manifest)} ({time.time()-t0:.0f}s, "
                      f"credits~{credits:.0f}, cached {cached}, errs {len(errs)})", flush=True)
    print(f"\nDone: {done} pages, cached {cached}, errors {len(errs)}, credits~{credits:.0f}")
    if errs:
        print("ERRORS:", json.dumps(errs[:10], indent=1))


if __name__ == "__main__":
    main()
