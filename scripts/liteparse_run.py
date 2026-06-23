#!/usr/bin/env python3
"""Run LiteParse (run-llama OSS, the open-sourced core of LlamaParse minus the VLM layer) over the
insurance-forms corpus and cache per-page reconstructed markdown.

LiteParse is a LOCAL, vision-blind, text-layer + spatial-grid parser (PDFium native text -> anchor
"grid projection" -> heuristic markdown with pipe tables/headings/lists; Tesseract OCR auto-triggers
only when native text is sparse). So we feed it the BORN-DIGITAL PDF (Data/*.pdf), its native input —
exactly like PyMuPDF reads the text layer via fitz. Forcing the PNG renders (as the vision vendors
need) would handicap it into pure OCR, which is unfair and is already covered by the Tesseract vendor.

Representation = per-page MARKDOWN (result.text on a single-page parse), LiteParse's flagship output
and its best foot forward — the direct analogue of LlamaParse's page-`md` path. The whole-document
markdown has no page delimiters, so we parse per page (resumable; free/local).

These are FORMS: the relevant question is whether LiteParse's grid projection keeps each filled-in
value next to its label and each tick next to its option, or flattens the page (which loses the
binding). The judges (fair-total + spatial) answer that.

Output: ground_truth/liteparse/raw/{doc}__p{page:04d}.md   (one markdown file per page)
Usage:  .venv-liteparse/bin/python scripts/liteparse_run.py    # uses the LiteParse interpreter
"""
import os, sys, json, time, glob

import liteparse

RENDER = "ground_truth/render_full"
RAW = "ground_truth/liteparse/raw"


def manifest():
    return json.load(open(os.path.join(RENDER, "_manifest.json")))


def pdfs():
    seen = {}
    for pat in ("Data/*.pdf", "Data/*.PDF"):  # macOS glob is case-sensitive (see corpus.py)
        for p in glob.glob(pat):
            seen.setdefault(os.path.splitext(os.path.basename(p))[0], p)
    return seen


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
            # OCR-trigger proxy: a page whose native grid text is near-empty fell back to OCR.
            pg = res.pages[0] if res.pages else None
            if pg is not None and len((pg.text or "").strip()) < 20:
                ocr_hits += 1
        except Exception as e:
            md = ""
            print(f"  [err] {doc} p{page}: {e}", file=sys.stderr)
        open(cp, "w").write(md)
        done += 1
        print(f"  {done}/{len(rows)}  {doc[:30]} p{page} ({len(md)} chars)", flush=True)
    print(f"done {done} pages in {time.time()-t0:.0f}s; "
          f"~{ocr_hits} sparse/OCR-candidate pages -> {RAW}")


if __name__ == "__main__":
    main()
