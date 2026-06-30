#!/usr/bin/env python3
"""Shared Pulse (runpulse.com) helpers: REST client, the per-page /extract call in Pulse's MOST
ADVANCED configuration, and the response->markdown reducer. Imported by pulse_run.py (the
full-corpus runner) and collect_extractions.collect_pulse() so the two NEVER diverge in how
Pulse's raw response is turned into a judged document. (Ported from the sibling insurance
benchmark; identical client/reducer, finance-tuned commentary.)

CONFIG = Pulse's MOST ADVANCED tier (per the project principle of giving each tool its best native
representation — LlamaParse on `agentic`, Landing AI on DPT-2, Mistral on mistral-ocr-4-0 — and the
user's explicit ask: "use their most advanced capability through config"):
  - model            = pulse-ultra-2  (Pulse's self-hosted flagship vision model, vs the `default`
                       tier; unlocks the refine + figure flags below).
  - refine           = true, with refine_options.{tables,text,formatting} all true — a full-page
                       re-OCR + formatting-correction pass (~1-2s/page of overhead per Pulse's docs;
                       empirically ~40-60s/page here). On the corpus probe this VISIBLY cleaned the
                       text vs `default` (correct accents, drops `default`'s per-element content
                       prefix garbage) and rebuilt table structure.
  - figure_processing.description = true -> 1-2 paragraph VLM description per figure, so graphics are
                       DESCRIBED WITH THEIR DATA (parallel to Mistral's bbox annotation / Landing-AI
                       figure chunks), not left as opaque boxes. On THIS corpus (chart-heavy M&A
                       memos, annual reports) this is the load-bearing flag — it is what lets Pulse
                       compete as a figure reader rather than score like a text-layer tool on the
                       Chart/Diagram pages. (CURRENT param; the older `extract_figure` /
                       `figure_description` flags are deprecated per the API's own response warnings.)

Response shape (probed 2026-06-30, pulse-ultra-2):
  markdown                top-level, CLEAN page markdown (tables inlined, headings/structure kept).
  bounding_boxes.Tables[] {cell_data:[{position:{row,column}, text, properties:{spans_columns,type}}]}
  bounding_boxes.Images[] {visual_type, chart_type, chart_title, description, image_url, ...}
  bounding_boxes.Words/Text/Header/Footer/SelectionMarks/ordered_elements/markdown_with_ids
  credits_used, page_count, extraction_id, plan_info

REDUCER decisions (mirroring the project's existing collectors, esp. mistral_common.reduce_page):
  - The top-level `markdown` IS the judged block (tables already inline), so — unlike Mistral — there
    is no placeholder-inlining to do. Used as the single ordered block (-> ordered_full, like the
    LlamaParse page-md / LiteParse path).
  - Each annotated image -> a figure {kind, content} (parallel to collect_landingai / collect_mistral
    figure chunks), so Pulse is fairly credited / penalised as a figure reader on the Chart pages.
  - `tables` reconstructs each Tables[] grid from cell_data (for the table-count diagnostic + numeric
    pool); the per-cell digits+tag prefix (e.g. "0t-") that Pulse emits on the bbox layer is stripped
    (the top-level markdown does NOT carry it, so the judged text is unaffected).
"""
import os, re, time, base64
import requests

BASE = os.environ.get("PULSE_BASE", "https://api.runpulse.com")
MODEL = os.environ.get("PULSE_MODEL", "pulse-ultra-2")
# bbox-layer cell-content prefix artifact, e.g. "0t-hebdomadaire", "0a-www.mnh.fr"
_CELL_PREFIX = re.compile(r"^\s*\d+[a-z]{1,2}-")
# Dotted/underscored leader RUNS ("Introduction ......... 5", "Nom : ............") that
# pulse-ultra-2 + refine can expand into runs of tens of thousands of literal leader chars. Pure
# leader noise, not content: because the runs start well inside the judge's 16K input cap they would
# push real content out of the judged window. Collapse each run to a single ellipsis (faithful: a
# leader line carries no information; other OCR vendors already collapse these). Solid runs and
# space-separated leaders both handled. Bullets (•‣◦▪) included: Pulse renders some graphic regions
# (e.g. a wall of customer logos) as a solid run of thousands of `•` — seen at 30,728 bullets on one
# SOTER page, blowing it to 32K chars of pure noise.
_FILLER = re.compile(r"(?:[.·•‣◦▪_]\s*){4,}")
# Generic catch-all for any OTHER symbol glyph (not word-char / whitespace / table pipe) repeated
# 10+ times in a row — a graphic-fill artifact carrying no information (runs of =, ■, ▬, —, etc.).
# Collapse to a single instance. Excludes `|` so table structure is untouched.
_GLYPH_RUN = re.compile(r"([^\w\s|])\1{9,}")
# Pulse occasionally renders a chart/graphic region as a GIANT EMPTY markdown table — a row of
# hundreds of blank `| | |` cells (seen once at 8,120 cells on a single Alpha page, blowing the page
# to 16K+ chars and burying the real content under the judge's input cap). A run of empty table cells
# carries no information, so collapse any run of 4+ consecutive EMPTY cells to a single empty cell
# (cells that hold content are untouched — `[^\S\n]` is horizontal whitespace only, so `| A | B |`
# never matches).
_EMPTY_CELLS = re.compile(r"(?:\|[^\S\n]*){4,}\|")


def api_key():
    if os.path.exists(".env"):
        for l in open(".env"):
            if l.startswith("PULSE_API_KEY="):
                v = l.split("=", 1)[1].strip()
                if v:
                    return v
    return os.environ["PULSE_API_KEY"]


def _form_fields():
    """The most-advanced config as multipart form fields (the encoding the API accepts; nested
    refine_options use bracket notation, verified HTTP 200 on probe)."""
    return [
        ("model", MODEL),
        ("refine", "true"),
        ("refine_options[tables]", "true"),
        ("refine_options[text]", "true"),
        ("refine_options[formatting]", "true"),
        ("figure_processing[description]", "true"),
    ]


def extract_call(png_path, retries=5, timeout=600):
    """One /extract call on a single page PNG in the advanced config. Returns (response_dict,
    wall_seconds). pulse-ultra-2 + refine is SLOW (~40-60s/page) and can rate-limit under concurrency,
    so the timeout is generous and we back off long on failure. Follows the large-result `is_url`
    download indirection defensively (single pages don't trigger it, but multi-page inputs would)."""
    key = api_key()
    last = None
    for a in range(retries):
        try:
            t0 = time.time()
            with open(png_path, "rb") as fh:
                r = requests.post(
                    f"{BASE}/extract",
                    headers={"x-api-key": key},
                    files={"file": (os.path.basename(png_path), fh, "image/png")},
                    data=_form_fields(),
                    timeout=timeout,
                )
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
            resp = r.json()
            if resp.get("is_url") and resp.get("url"):
                d = requests.get(resp["url"], headers={"x-api-key": key}, timeout=timeout)
                d.raise_for_status()
                resp = d.json()
            return resp, time.time() - t0
        except Exception as e:
            last = e
            time.sleep(min(60, 8 * (2 ** a)))  # 8,16,32,60,60 — rides out 429 / transient bursts
    raise RuntimeError(f"Pulse /extract failed after {retries} tries: {last}")


def _table_text(tbl):
    """Reconstruct one Tables[] entry to tab/newline text from its cell_data grid (prefix stripped)."""
    cells = tbl.get("cell_data") or []
    rows = {}
    for c in cells:
        pos = c.get("position") or {}
        r, col = pos.get("row", 0), pos.get("column", 0)
        txt = _CELL_PREFIX.sub("", (c.get("text") or "")).strip()
        rows.setdefault(r, {})[col] = txt
    lines = []
    for r in sorted(rows):
        cols = rows[r]
        lines.append("\t".join(cols[k] for k in sorted(cols)))
    return "\n".join(lines).strip()


def reduce_response(resp):
    """One Pulse /extract response -> (judged_markdown, table_text_list, figures).
      judged_markdown : top-level `markdown` (tables inline). Clean.
      tables          : list of reconstructed table text strings (table-count diagnostic + num pool).
      figures         : [{kind, content}] from each annotated image (parallel to mistral figures).
                        Images with no description/title are dropped (no credit for empty boxes).
    """
    md = (resp.get("markdown") or "").strip()
    md = _FILLER.sub("…", md)
    md = _GLYPH_RUN.sub(r"\1", md)
    md = _EMPTY_CELLS.sub("| |", md)
    # an all-empty table row left after collapse (just `| |`) carries nothing — drop it
    md = "\n".join(ln for ln in md.splitlines() if ln.strip(" |") or "|" not in ln)
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    bb = resp.get("bounding_boxes") or {}
    tables = []
    for t in (bb.get("Tables") or []):
        tt = _table_text(t)
        if tt:
            tables.append(tt)
    figures = []
    for im in (bb.get("Images") or []):
        if not isinstance(im, dict):
            continue
        kind = im.get("chart_type") or im.get("visual_type") or "figure"
        desc = (im.get("description") or im.get("chart_title") or "").strip()
        if not desc:
            continue
        figures.append({"kind": kind, "content": desc})
    return md, tables, figures
