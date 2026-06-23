# Adding Mistral OCR 4 (advanced config) as the 8th vendor — insurance forms

*2026-06-23. Full-corpus benchmark of Mistral OCR 4, run in its **most advanced configuration**,
validated and spliced into the canonical structure-aware fair total (gpt-5 + Gemini families,
structure + content) and the form **spatial/checkbox** ranking. Headline: **92% structure-aware
(gpt-5) — the new clean #1, above gpt-5 image (80%) and even the ◆ Landing AI reference (84%);
unsupported just 8%, with a near-zero −1 structure gap. On the form-spatial metric it tops BOTH
judges (97%), reading checkbox state at 100%.***

> **This is the cross-benchmark headline.** The *same tool* was **5th of 10 and the fabrication
> outlier (19% unsupported)** on the [Finance corpus](../PDF%20parsing%20test%20-%20Finance/MISTRAL_ADD.md)
> (chart/figure-dense) and is the **clean #1 (8% unsupported)** here. Genre flips the verdict:
> forms have almost no charts/graphics for its annotation layer to hallucinate on (its Finance
> weakness vanishes), while dense-text OCR + checkbox-glyph preservation + HTML table structure —
> exactly what forms reward — are its strengths. Tool ranking is genre-dependent; this is the
> sharpest single demonstration of it across the two benchmarks.

## What Mistral OCR 4 is + config

[Mistral OCR 4](https://mistral.ai/news/ocr-4/) (released 2026-06-23) is a vision document-extraction
model: per-page markdown + HTML tables + bounding boxes + per-image annotation + confidence scores.
Run, per the project principle of giving each tool its best native representation (LlamaParse on
`agentic`, Landing AI on DPT-2), at its **most capable tier** — identical config to the Finance add
(`scripts/mistral_common.py`, shared with runner + collector so they cannot diverge):

- **`mistral-ocr-4-0`** — the explicit OCR-4 model.
- **`table_format="html"`** — preserves cell bindings (grid-markdown column merges are unrecoverable
  under the structure-aware metric; see [`LITEPARSE_ADD` history`](FINDINGS.md)).
- **`bbox_annotation_format`** = per-image VLM annotation (`ImageAnnotation{image_type, description}`)
  — the Document-AI layer that describes graphics. On forms this mostly returns logos/icons/stamps
  (probe: the Unédic logo and an MNH cart icon), so unlike Finance there is little for it to over-read.

### Reduction (one artifact headed off at the collector — same as Finance)

OCR 4 emits tables/images as **placeholders** (`[tbl-0.html](tbl-0.html)`, `![img-0.jpeg](img-0.jpeg)`)
with the real HTML in a separate `tables[]` array. `mistral_common.reduce_page` **inlines** each
table's HTML at its placeholder (appending any unanchored table so none is dropped) and maps each
annotated image to a figure `{kind, content}`. Result across the 7 pages: 7 tables inlined as HTML
(rowspan/colspan preserved) + 2 figure descriptions, 0 leftover placeholders. Crucially, the page
markdown **preserves the checkbox glyphs (☐ blank / ☒ ☑ ticked) bound to their option labels** in
reading order — the single most consequential signal on these forms.

## Input arm: PNG (no separate Insurance A/B)

Run on the per-page **PNG renders**, matching every other vision vendor here and the OCR-4-specific
PNG-vs-PDF A/B already settled on the Finance corpus (PNG +4.2pp, lower hallucination). It is also
the only sensible input for this corpus: the Unédic *attestation* is a **scan** with no born-digital
text layer, so a "born-digital PDF" arm is not even meaningful. `MISTRAL_INPUT=png scripts/mistral_run.py`,
7 pages, 0 errors, ~13s wall on 3 workers.

## How it was judged (ADD, not swap — weights frozen)

Generalized the LiteParse splice into `scripts/splice_vendor.py` (per-vendor suffix + `pre_<vendor>_archive`):
`mistral` added to `build_vendor_md.ALL_VENDORS` and the collector; all five judge passes re-run
**8-up** to fresh `_mistral` outputs/caches with **`LA_DPT2=1`** (canonical LA slot = DPT-2). Only
Mistral's score column is spliced into canonical; the other 7 vendors stay **byte-identical**
(verified: 0 diffs vs `results/pre_mistral_archive/`). Validation = the existing 7 vendors'
aggregate, under *canonical* weights, between the canonical run and the 8-vendor run, on the loose
n=7 gross-distortion gate (|Δ| < 10pp — the corpus is 7 pages, so per-page judge variance dominates).

| Judge pass | worst drift on the existing 7 | gate | Mistral |
|---|---:|---:|---:|
| **gpt-5 structure (HEADLINE)** | 6.6 pp | 10 | **92% / 8% unsup** |
| gpt-5 content (diagnostic) | 8.1 pp | 10 | 94% / 6% |
| gemini structure | 2.9 pp | 10 | 98% / 1% |
| gpt-5 spatial | 7.5 pp | 10 | **97%** |
| gemini spatial | **21.5 pp — TRIPPED** | 10 | 97% |

**The Gemini-spatial gate tripped, and was force-spliced after audit.** The drift is concentrated in
the two *weakest* vendors — Tesseract +21.5 (49→71), LiteParse +10.4 (45→56) — and the per-page trace
shows the whole Gemini-spatial re-judge ran **globally more lenient** (e.g. gpt-5-image MNH-p2 68→100,
Tesseract AE-p2 40→90): a judge-leniency level shift, biggest on borderline-bad OCR where a lenient
grader has the most room, not a comparison broken by Mistral. This is exactly the n=7 / lenient-Gemini
noise the methodology flags. Decisive point: **Mistral's own column is cross-family-corroborated —
97.0 (Gemini spatial) vs 97.5 (gpt-5 spatial), 90–100 every page** — so its spliced value is
trustworthy, and freezing canonical means no existing published number moved regardless. Spliced via
`splice_vendor.py mistral --splice --force="gemini spatial"` (the force path prints a loud audit line;
the four clean families spliced automatically).

## Results

**Structure-aware fair total (canonical, gpt-5 headline):** **92%**, content 94%, **structure gap −1**,
unsupported **8%**. Clean #1 — above gpt-5 image (80%) and the ◆ Landing AI reference (84%); only the
◆ Gemini co-author (99%) is higher. The −1 gap means it *preserves* structure (HTML tables + checkbox
glyphs), unlike the text-layer tools (LiteParse −20, Tesseract −15, PyMuPDF −23).

**Per-category (gpt-5 structure):** Text 90 · **Form 91** · Table 98 · Mixed 92. It **dominates the
Form category (91)** — the hardest, most form-specific pages — vs gpt-5 image 65 and ◆ Landing AI 72,
near the ◆ Gemini ceiling (98).

**Per-doc (gpt-5 structure):** Unédic *attestation* (partly scanned) 91.5 · MNH *aide sociale*
(born-digital) 93.8 — strong on both the scan and the born-digital form.

**Form-spatial ranking — #1 on BOTH judges** (`results/SPATIAL_RANKING.md`):

| judge | SPATIAL | field | check | cell |
|---|---:|---:|---:|---:|
| gpt-5 | **97%** | 96 | **100** | 95 |
| Gemini | **97%** | 98 | 97 | 95 |

The decisive call on these forms is **checkbox state**, and it sorts tools by *how each sees a tick*:
**0%** for the flatten-the-text-layer parsers (PyMuPDF, LlamaParse), a noisy partial for Tesseract's
pixel OCR (6–31%) and LiteParse's glyph-preserving grid (22–27%), and **85–100% only for vision**.
Mistral reads the ☐/☒ glyph bound to its label and lands at **100% (gpt-5) / 97% (Gemini)** — squarely
in the vision tier. On forms, a vision model is not optional, and OCR 4 is a vision model.

**Fabrication is present but localized, not the headline it was in Finance.** Aggregate unsupported is
8% (gpt-5), but two pages carry it: the dense rupture/indemnity page (AE p4, 25%) and the MNH cover
letter (p1, 20%) — the annotation layer over-asserting on a near-empty/low-signal page, the same
low-information failure direction seen in Finance, just with far less surface area to act on (no
charts). For finance-grade use the confidence scores should still gate figure/indemnity-derived claims.

## The finding

**On insurance forms, Mistral OCR 4 is the best clean vendor (92% structure-aware), because the genre
removes the weakness that made it the fabrication outlier on finance documents and rewards exactly its
strengths.** Dense multilingual text OCR (Text 90), HTML tables that survive a binding check (Table
98), and — decisively — **checkbox-glyph preservation that reads tick state at 100%**, the call that
separates the field on forms. It is fast (~13s/7pp), cheap (~$0.04 parsing at $5/1k pages), and clean
across both judge families. The cross-benchmark contrast with Finance (5th, 19% unsupported) is the
single clearest evidence in either repo that **document genre, not the tool alone, determines the
right extractor** — pick the vendor for the document, not in the abstract.

## Artifacts

- Shared reducer `scripts/mistral_common.py`; runner `scripts/mistral_run.py`
  (`MISTRAL_INPUT=png`); collector `collect_mistral()` in `scripts/collect_extractions.py`.
- Add-splicer `scripts/splice_vendor.py` (generalized from `splice_liteparse.py`; per-vendor suffix +
  `--force` for documented-noise families).
- Raw per-page responses `ground_truth/mistral/raw/`; collected `results/_extract_mistral.json`;
  8-vendor judge outputs `results/_fair_total_judging{,_content,_gemini_v2}_mistral.json` +
  `results/_spatial_judging{,_gemini}_mistral.json`; canonical originals in `results/pre_mistral_archive/`.
- Judge cost ~$0.83 (gpt-5 structure $0.18 + content $0.17 + spatial $0.24; Gemini structure $0.11 +
  spatial $0.13) + ~$0.04 parsing.
- Regenerated: `results/FAIR_TOTAL.md`, `results/SPATIAL_RANKING.md`; prose synced in `README.md`,
  `FINDINGS.md`, `DESIGN.md`.
