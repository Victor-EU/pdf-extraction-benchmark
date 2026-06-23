#!/usr/bin/env python3
"""A/B follow-up: DPT-2 on native PDF PAGES vs DPT-2 on PNGs (vs legacy).

Tests the one lever the first A/B could not: does giving DPT-2 the born-digital PDF page (vector
text + exact glyph coordinates) instead of a rasterized PNG recover the table-structure losses
(p90 flattened its columns)? Uses the SAME 15 SOTER pages as the PNG run, each extracted as a
single-page PDF (isolates input medium; per-page granularity matches the PNG run exactly).

Usage:  python3 scripts/ab_landingai_dpt2_pdf.py [limit]
Output: ground_truth/landingai_dpt2_pdf_ab/{raw/*.json, page_pdf/*.pdf, extract.json}
"""
import os, sys, json, time, requests, fitz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ab_landingai_dpt2 import api_key, clean_md, reconstruct, PARSE_URL, MODEL, DOC

SRC_PDF = f"Data/{DOC}.pdf"
PNG_RUN = "ground_truth/landingai_dpt2_ab/extract.json"     # same pages as the PNG A/B
OUT = "ground_truth/landingai_dpt2_pdf_ab"


def extract_page_pdf(src_doc, page1, dst):
    """Write a single-page PDF (page1 is 1-indexed) preserving the vector/text content."""
    out = fitz.open()
    out.insert_pdf(src_doc, from_page=page1 - 1, to_page=page1 - 1)
    out.save(dst)
    out.close()


def call_parse_pdf(pdf_path, key, retries=4):
    headers = {"Authorization": f"Bearer {key}"}
    last = None
    for a in range(retries):
        try:
            with open(pdf_path, "rb") as f:
                files = {"document": (os.path.basename(pdf_path), f, "application/pdf")}
                data = {"model": MODEL, "split": "page"}
                t0 = time.time()
                r = requests.post(PARSE_URL, headers=headers, files=files, data=data, timeout=180)
            wall = time.time() - t0
            if r.status_code == 200:
                return r.json(), wall, None
            last = f"HTTP {r.status_code}: {r.text[:400]}"
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** a + 1)
                continue
            return None, 0, last
        except Exception as e:
            last = str(e)
            time.sleep(2 ** a + 1)
    return None, 0, last


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    key = api_key()
    raw_dir = os.path.join(OUT, "raw"); pdf_dir = os.path.join(OUT, "page_pdf")
    os.makedirs(raw_dir, exist_ok=True); os.makedirs(pdf_dir, exist_ok=True)
    pages = [(r["page"], r["cat"]) for r in json.load(open(PNG_RUN))]
    if limit:
        pages = pages[:limit]
    src = fitz.open(SRC_PDF)
    print(f"DPT-2 PDF-page A/B over {len(pages)} SOTER pages")
    records = []
    for page, cat in pages:
        pdf_path = os.path.join(pdf_dir, f"{DOC}__p{page:04d}.pdf")
        raw_path = os.path.join(raw_dir, f"{DOC}__p{page:04d}.pdf.json")
        if not os.path.exists(pdf_path):
            extract_page_pdf(src, page, pdf_path)
        if os.path.exists(raw_path):
            resp = json.load(open(raw_path)); wall = resp.get("_wall")
        else:
            resp, wall, err = call_parse_pdf(pdf_path, key)
            if resp is None:
                print(f"  p{page} ERROR {err}"); continue
            resp["_wall"] = wall
            json.dump(resp, open(raw_path, "w"))
        chunks = resp.get("chunks", [])
        native = clean_md(resp.get("markdown", ""))
        chunk_md = reconstruct(chunks)
        credit = (resp.get("metadata", {}) or {}).get("credit_usage")
        records.append({"doc": DOC, "page": page, "cat": cat, "native_md": native,
                        "chunk_md": chunk_md, "n_chunks": len(chunks), "credit": credit,
                        "wall": round(wall, 2) if wall else None})
        print(f"  p{page:<4} {cat:<14} chunks={len(chunks):<3} native={len(native):<6} "
              f"credit={credit} {wall and round(wall,1)}s")
    json.dump(records, open(os.path.join(OUT, "extract.json"), "w"), indent=2)
    tot = sum(r["credit"] for r in records if r.get("credit"))
    print(f"\nWrote {len(records)} pages -> {OUT}/extract.json  total credit={tot}")


if __name__ == "__main__":
    main()
