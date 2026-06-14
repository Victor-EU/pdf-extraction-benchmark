#!/usr/bin/env python3
"""LlamaParse AGENTIC-tier pass — LlamaParse's MOST CAPABLE mode (matches the prior
pdf-extraction-audit, which scored 87.8% on IAR with tier='agentic').

The original benchmark used `accurate` mode (a middle tier), which catastrophically
dropped whole pages (e.g. IAR p228-237, the auditor's report) on this born-digital
corpus. This re-runs the same 3 PDFs at tier='agentic' so the published numbers reflect
the vendor's best solution. Saves raw per-doc JSON in the SAME shape as the accurate raw
(pages[] with page/md/text/items/...) so collect_extractions.py works unchanged.

Output: ground_truth/llamaparse_agentic/raw/{doc}.json  (resumable per doc)
"""
import os, sys, json, time

DOCS = {
    "20190308_Projet_Alpha_Restitution": "Data/20190308_Projet_Alpha_Restitution.pdf",
    "IAR_FY25_EN": "Data/IAR_FY25_EN.pdf",
    "SOTER - Company Presentation - vFF": "Data/SOTER - Company Presentation - vFF.pdf",
}


def key():
    for l in open(".env"):
        if l.startswith("LLAMA_CLOUD_API_KEY="):
            return l.split("=", 1)[1].strip()
    raise SystemExit("no LLAMA_CLOUD_API_KEY in .env")


def main():
    from llama_cloud_services import LlamaParse
    out_dir = "ground_truth/llamaparse_agentic/raw"
    os.makedirs(out_dir, exist_ok=True)
    api_key = key()
    summary = {}
    for doc, path in DOCS.items():
        raw_path = os.path.join(out_dir, doc + ".json")
        if os.path.exists(raw_path):
            d = json.load(open(raw_path))
            print(f"[cached] {doc}: {len(d.get('pages',[]))} pages", flush=True)
            summary[doc] = {"pages": len(d.get("pages", [])), "wall_s": d.get("_wall_s")}
            continue
        print(f"[parse:agentic] {doc} ...", flush=True)
        t0 = time.time()
        p = LlamaParse(api_key=api_key, tier="agentic", version="latest",
                       result_type="markdown")
        res = p.parse(path)
        pages = [pg.model_dump() for pg in res.pages]
        # normalize: ensure 1-indexed 'page' int matches our key (SDK uses .page)
        for i, pg in enumerate(pages):
            if not pg.get("page"):
                pg["page"] = i + 1
        data = {"pages": pages, "_wall_s": round(time.time() - t0, 1),
                "_job_id": getattr(res, "job_id", None), "_tier": "agentic"}
        json.dump(data, open(raw_path, "w"))
        print(f"  saved {raw_path}: {len(pages)} pages, wall={data['_wall_s']}s", flush=True)
        summary[doc] = {"pages": len(pages), "wall_s": data["_wall_s"]}
    print("\nSUMMARY:", json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
