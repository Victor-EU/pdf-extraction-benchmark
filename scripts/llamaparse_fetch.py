#!/usr/bin/env python3
"""LlamaParse (LlamaCloud) pass: upload each source PDF once, poll, save raw JSON result.

Parses whole documents (not per-page) — LlamaParse returns per-page structured output
(items typed heading/text/table with bBox, plus separate `charts` and `images` arrays).
Saves raw per-doc JSON to ground_truth/llamaparse/raw/{doc}.json (resumable).
Category reduction is a separate offline step (llamaparse_reduce.py) so thresholds can be
iterated without re-spending credits.
"""
import os, sys, time, json, requests, certifi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import discover_pdfs

BASE = "https://api.cloud.llamaindex.ai/api/v1/parsing"


def key():
    for l in open(".env"):
        if l.startswith("LLAMA_CLOUD_API_KEY="):
            return l.split("=", 1)[1].strip()
    raise SystemExit("no LLAMA_CLOUD_API_KEY in .env")


def main():
    H = {"Authorization": f"Bearer {key()}", "accept": "application/json"}
    out_dir = "ground_truth/llamaparse/raw"
    os.makedirs(out_dir, exist_ok=True)
    summary = {}
    for doc, path in discover_pdfs().items():
        raw_path = os.path.join(out_dir, doc + ".json")
        if os.path.exists(raw_path):
            data = json.load(open(raw_path))
            print(f"[cached] {doc}: {len(data.get('pages',[]))} pages")
            summary[doc] = {"pages": len(data.get("pages", [])),
                            "credits": data.get("job_metadata", {}).get("credits_used"),
                            "wall_s": data.get("_wall_s")}
            continue
        print(f"[upload] {doc} ({path}) ...")
        t0 = time.time()
        with open(path, "rb") as f:
            r = requests.post(BASE + "/upload", headers=H,
                              files={"file": (os.path.basename(path), f, "application/pdf")},
                              verify=certifi.where(), timeout=300)
        r.raise_for_status()
        jid = r.json()["id"]
        print(f"  job {jid}; polling...")
        st = None
        for _ in range(400):
            s = requests.get(f"{BASE}/job/{jid}", headers=H, verify=certifi.where(), timeout=60).json()
            st = s.get("status")
            if st in ("SUCCESS", "PARTIAL_SUCCESS", "COMPLETED", "ERROR"):
                break
            time.sleep(4)
        print(f"  status={st} after {time.time()-t0:.0f}s")
        if st == "ERROR":
            print("  ERROR:", json.dumps(s)[:300]); continue
        jr = requests.get(f"{BASE}/job/{jid}/result/json", headers=H, verify=certifi.where(), timeout=300)
        jr.raise_for_status()
        data = jr.json()
        data["_wall_s"] = round(time.time() - t0, 1)
        data["_job_id"] = jid
        json.dump(data, open(raw_path, "w"))
        cr = data.get("job_metadata", {}).get("credits_used")
        print(f"  saved {raw_path}: {len(data.get('pages',[]))} pages, credits={cr}, wall={data['_wall_s']}s")
        summary[doc] = {"pages": len(data.get("pages", [])), "credits": cr, "wall_s": data["_wall_s"]}
    print("\nSUMMARY:", json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
