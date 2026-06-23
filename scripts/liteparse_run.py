#!/usr/bin/env python3
"""Run LiteParse (run-llama OSS, the open-sourced core of LlamaParse minus the VLM layer) over the
599-page corpus and cache per-page reconstructed markdown.

LiteParse is a LOCAL, vision-blind, text-layer + spatial-grid parser (PDFium native text -> anchor
"grid projection" -> heuristic markdown with pipe tables/headings/lists; Tesseract OCR auto-triggers
only when native text is sparse). So we feed it the BORN-DIGITAL PDF (Data/*.pdf), its native input —
exactly like PyMuPDF reads the text layer via fitz. Forcing the PNG renders (as the vision vendors
need) would handicap it into pure OCR, which is unfair and is already covered by the Tesseract vendor.

Representation = per-page MARKDOWN (result.text on a single-page parse), LiteParse's flagship output
and its best foot forward — the direct analogue of LlamaParse's page-`md` path. The whole-document
markdown has no page delimiters, so we parse per page (resumable; ~10 min once, free/local).

Output: ground_truth/liteparse/raw/{doc}__p{page:04d}.md   (one markdown file per page)
Usage:  python3 scripts/liteparse_run.py            # uses the .venv-liteparse interpreter
"""
import os, sys, json, time, glob

import liteparse

RENDER = "ground_truth/render_full"
RAW = "ground_truth/liteparse/raw"


def manifest():
    return json.load(open(os.path.join(RENDER, "_manifest.json")))


def pdfs():
    return {os.path.splitext(os.path.basename(p))[0]: p for p in glob.glob("Data/*.pdf")}


def main():
    os.makedirs(RAW, exist_ok=True)
    P = pdfs()
    rows = manifest()
    t0 = time.time()
    done = ocr_hits = 0
    for m in rows:
        doc, page = m["doc"], m["page"]
        cp = os.path.join(RAW, f"{doc}__p{page:04d}.md")
        if os.path.exists(cp):
            done += 1
            continue
        parser = liteparse.LiteParse(output_format="markdown", target_pages=str(page),
                                     quiet=True)
        try:
            res = parser.parse(P[doc])
            md = res.text or ""
            # OCR-trigger heuristic: a page whose native text layer is sparse falls back to OCR.
            # We can't read the engine flag from the wheel, so flag pages where the grid text is
            # near-empty (a proxy LiteParse itself uses to decide OCR) for the report.
            pg = res.pages[0] if res.pages else None
            if pg is not None and len((pg.text or "").strip()) < 20:
                ocr_hits += 1
        except Exception as e:
            md = ""
            print(f"  [err] {doc} p{page}: {e}", file=sys.stderr)
        open(cp, "w").write(md)
        done += 1
        if done % 25 == 0:
            print(f"  {done}/{len(rows)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"done {done} pages in {time.time()-t0:.0f}s; "
          f"~{ocr_hits} sparse/OCR-candidate pages -> {RAW}")


if __name__ == "__main__":
    main()
