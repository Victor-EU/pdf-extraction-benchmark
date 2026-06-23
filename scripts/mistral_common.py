#!/usr/bin/env python3
"""Shared Mistral OCR-4 helpers: API client, the per-page OCR call (PNG or born-digital PDF
input), and the page->markdown reducer. Imported by ab_mistral_input.py (the input A/B),
mistral_run.py (the full-corpus runner) and collect_extractions.collect_mistral() so the three
NEVER diverge in how OCR-4's raw response is turned into a judged document.

CONFIG = OCR-4's MOST ADVANCED tier (per user: best foot forward, like running LlamaParse on
`agentic` not `accurate` and Landing AI on DPT-2 not legacy):
  - model = mistral-ocr-4-0 (the explicit OCR-4 model, advanced features).
  - table_format = html (preserves cell bindings; grid-markdown's column merges are unrecoverable
    under the structure-aware metric — see LITEPARSE_ADD.md).
  - bbox_annotation_format = ImageAnnotation schema -> the Document-AI per-image VLM annotation,
    so chart/figure GRAPHICS are DESCRIBED WITH THEIR DATA (chart type, axes, series, values,
    trend; diagram nodes + relationships), not left as opaque boxes. This is what makes OCR-4 a
    real figure reader, comparable to gpt-5/Gemini/Landing-AI/LlamaParse-agentic.

Response shape (probed 2026-06-23, mistral-ocr-4-0):
  pages[].markdown            text WITH placeholder refs: `[tbl-0.html](tbl-0.html)` for tables,
                              `![img-0.jpeg](img-0.jpeg)` for images.
  pages[].tables[]            {id, content} where content is the table as HTML (table_format=html).
  pages[].images[]            {id, bbox, image_base64:null, image_annotation:{image_type,description}}
  pages[].confidence_scores   {average/minimum_page_confidence_score, word_confidence_scores}

REDUCER decisions (mirroring the project's existing collectors):
  - INLINE each table's HTML into the markdown in place of its `[id](id)` placeholder. Without this
    the judge sees only a dead placeholder and OCR-4 gets ZERO table credit (a measurement artifact
    of exactly the kind this benchmark keeps catching). Any table whose placeholder isn't found is
    appended so it is never silently dropped.
  - Each annotated image -> a figure {kind: image_type, content: description}, exactly like
    collect_landingai's figure chunks / collect_gpt5's figure blocks. build_vendor_md.page_md
    appends these to the page md for the fair-total judge, and the figure judge reads them directly.
    The image PLACEHOLDER `![id](id)` is stripped from the md (the description carries the content).
"""
import os, re, time, base64
import fitz  # PyMuPDF, for splitting one born-digital page out for the PDF-input arm
from pydantic import BaseModel, Field

MODEL = os.environ.get("MISTRAL_MODEL", "mistral-ocr-4-0")
_IMG_PLACEHOLDER = re.compile(r"!\[[^\]]*\]\([^)]*\)")


class ImageAnnotation(BaseModel):
    """Per-image (bbox) annotation schema — pulls the chart/diagram DATA out of the graphic."""
    image_type: str = Field(description="chart, diagram, photo, logo, icon, map, or screenshot")
    description: str = Field(description=(
        "Thorough description of the image. If a data chart: state chart type, title, axis labels "
        "and scales, every series, and ALL data values/numbers and the trend. If a diagram/flow/"
        "org chart: list every node/box label and the relationships or flow between them. "
        "If a photo/logo/icon with no data, one short sentence."))


def api_key():
    if os.path.exists(".env"):
        for l in open(".env"):
            if l.startswith("MISTRAL_API_KEY="):
                v = l.split("=", 1)[1].strip()
                if v:
                    return v
    return os.environ["MISTRAL_API_KEY"]


def client():
    from mistralai.client import Mistral
    return Mistral(api_key=api_key())


def png_datauri(path):
    return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()


def page_pdf_datauri(pdf_path, page):
    """Extract a single (1-based) page as its own born-digital PDF -> base64 data URI, so OCR-4
    reads that page's native text layer and returns exactly one page (clean per-page attribution)."""
    src = fitz.open(pdf_path)
    nd = fitz.open()
    nd.insert_pdf(src, from_page=page - 1, to_page=page - 1)
    b = nd.tobytes()
    nd.close(); src.close()
    return "data:application/pdf;base64," + base64.b64encode(b).decode()


def _bbox_format():
    from mistralai.extra import response_format_from_pydantic_model
    return response_format_from_pydantic_model(ImageAnnotation)


def ocr_call(cl, document, retries=7):
    """One OCR-4 call in the advanced config: model=mistral-ocr-4-0, table_format=html, per-image
    bbox annotation (chart/figure data described), page-level confidence. Returns
    (response_dict, wall_seconds). The annotation tier rate-limits aggressively (429); back off
    long enough (capped 60s) that a concurrent burst doesn't exhaust retries in lockstep."""
    last = None
    for a in range(retries):
        try:
            t0 = time.time()
            r = cl.ocr.process(model=MODEL, document=document,
                               table_format="html",
                               bbox_annotation_format=_bbox_format(),
                               confidence_scores_granularity="page",
                               include_image_base64=False)
            return r.model_dump(), time.time() - t0
        except Exception as e:
            last = e
            time.sleep(min(60, 4 * (2 ** a)))      # 4,8,16,32,60,60,60 — rides out 429 bursts
    raise RuntimeError(f"OCR failed after {retries} tries: {last}")


def reduce_page(page):
    """One OCR-4 page dict -> (judged_markdown, table_html_list, figures).
      judged_markdown : page markdown with each table's HTML inlined at its placeholder and image
                        placeholders stripped (figure content travels in `figures`).
      tables          : list of table HTML strings (for the `tables` field / table counts).
      figures         : [{kind, content}] from each image's bbox annotation (parallel to
                        collect_landingai figure chunks). Images with no/empty annotation are dropped.
    """
    md = page.get("markdown") or ""
    tables = [t.get("content", "") or "" for t in (page.get("tables") or [])]
    for t in (page.get("tables") or []):
        tid = t.get("id"); content = t.get("content", "") or ""
        if not tid or not content:
            continue
        ph = f"[{tid}]({tid})"
        if ph in md:
            md = md.replace(ph, content)
        else:
            md += "\n\n" + content            # never drop a table the placeholder didn't anchor
    md = _IMG_PLACEHOLDER.sub("", md)
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    figures = []
    for im in (page.get("images") or []):
        ann = im.get("image_annotation")
        if isinstance(ann, str):
            import json as _json
            try:
                ann = _json.loads(ann)
            except Exception:
                ann = {"description": ann}
        if not isinstance(ann, dict):
            continue
        desc = (ann.get("description") or "").strip()
        if not desc:
            continue
        figures.append({"kind": ann.get("image_type", "figure"), "content": desc})
    return md, tables, figures


def full_page_md(md, figures):
    """The full judged page text: body md + figure descriptions appended, byte-identical to how
    build_vendor_md.page_md assembles a page from an _extract record. Used by the input A/B (which
    bypasses the _extract pipeline)."""
    parts = [md] + [f"[{f.get('kind','figure')}] {f.get('content','')}".strip() for f in figures]
    return "\n".join(p for p in parts if p and p.strip()).strip()
