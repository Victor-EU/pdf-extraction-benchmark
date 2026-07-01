# Adding Mistral OCR 4 (advanced config) as the 10th vendor

*2026-06-23. Full-corpus benchmark of Mistral OCR 4, run in its **most advanced configuration**,
validated and spliced into the canonical fair-total (both judge families, structure-aware + content)
and the figure eval. Headline: **80% structure-aware (gpt-5) — 5th among real vendors, vision tier,
+12 over PyMuPDF — but the highest unsupported rate of any vendor (19%): its chart/figure annotation
fabricates on graphics it can't read.***

> **Update 2026-06-30:** Pulse's addition as the 11th vendor moves Mistral to **6th among real
> vendors** (Pulse joins the 86 tier above it). The ranks in this dated add-trail are as of
> 2026-06-23; the scores are unchanged.

## What Mistral OCR 4 is

[Mistral OCR 4](https://mistral.ai/news/ocr-4/) (released 2026-06-23) is a vision document-extraction
model: per-page markdown + HTML tables + bounding boxes + per-image annotation + confidence scores,
170 languages, $4/1k pages base ($2 batch) / $5/1k for the Document-AI annotation layer. Mistral's own
headline cites a customer (Rogo) benchmark: "equivalent accuracy [to leading agentic parsers] at
roughly 8x lower cost and 17x lower latency" on a chart/figure-dense financial QA dataset — exactly
this benchmark's hardest genre, so this is the independent test of that claim.

## Config = the most advanced tier (best foot forward)

Per the project principle of giving each tool its best native input + representation (LlamaParse on
`agentic` not `accurate`; Landing AI on DPT-2 not legacy), OCR 4 was run at its most capable setting:

- **`mistral-ocr-4-0`** (the explicit OCR-4 model, advanced features).
- **`table_format="html"`** — preserves cell bindings. (Grid-markdown's column merges are unrecoverable
  under the structure-aware metric; see [`LITEPARSE_ADD.md`](LITEPARSE_ADD.md).)
- **`bbox_annotation_format`** = a per-image VLM annotation schema (`ImageAnnotation{image_type,
  description}`) — the **Document-AI layer that DESCRIBES chart/figure graphics WITH their data**
  (chart type, axes, series, values, trend; diagram nodes + relationships). This is what makes OCR 4
  a real figure reader, comparable to gpt-5/Gemini/Landing-AI/LlamaParse-agentic rather than a
  text-layer tool. (Probe: SOTER p7's line chart came back with axis scale + per-decade values;
  p9's value-chain as a full node-and-relationship list.)

Without the annotation layer, base OCR 4 returns chart regions as opaque bounding boxes (no data) —
that tier would have scored like a text-layer tool on figures. The advanced tier is the fair entry.

### One artifact headed off at the collector

OCR 4's markdown references tables/images as **placeholders** (`[tbl-0.html](tbl-0.html)`,
`![img-0.jpeg](img-0.jpeg)`), with the real table HTML in a separate `tables[]` array and image
descriptions in `images[].image_annotation`. Serving the markdown verbatim would have given OCR 4
**zero table credit** — a measurement artifact of exactly the kind this benchmark keeps catching.
`mistral_common.reduce_page` **inlines** each table's HTML at its placeholder (appending any
unanchored table so none is dropped) and maps each annotated image to a figure `{kind, content}`
(parallel to `collect_landingai`'s figure chunks). Result: 310 tables + 714 figure descriptions
across the corpus, 0 leftover placeholders.

## Input A/B: PNG vs born-digital PDF → PNG

OCR 4 accepts both rasterized PNG pages and born-digital PDF. A 24-page stratified A/B
(`ab_mistral_input.py` + `ab_score_mistral_input.py`, canonical gpt-5 structure judge, both arms
reduced identically) settled it the same way the Landing AI DPT-2 input choice was settled:

| arm | recall | unsupported | Text | Table | Mixed | Chart |
|---|---:|---:|---:|---:|---:|---:|
| **PNG** | **83.2** | **15.4** | 97.5 | 92.8 | 82.5 | 58.4 |
| born-digital PDF | 79.0 | 20.6 | 97.9 | 92.8 | 76.1 | 53.4 |

**PNG wins by 4.2pp with lower hallucination** (and wins or ties every category) — same direction as
the DPT-2 finding. The full corpus was parsed from the per-page PNG renders, matching every other
vision vendor.

## How it was run

- `pip install mistralai pymupdf` into `.venv-mistral`; key in `.env` as `MISTRAL_API_KEY`.
- `scripts/mistral_run.py` (`MISTRAL_INPUT=png`) → resumable per-page cache
  `ground_truth/mistral/raw/{doc}__p{page}.json`. 599 pages, 0 errors. The annotation tier
  rate-limits aggressively (429 in concurrent bursts); settled at **3 workers** with capped
  exponential backoff (787s clean; ~5.2s/page median latency — the slowest vendor here, the
  annotation VLM pass is the cost).
- `collect_mistral()` in `collect_extractions.py` via the shared `mistral_common.reduce_page`
  (same reducer as the runner + A/B, so they cannot diverge) → `results/_extract_mistral.json`.

## How it was judged (add, not swap — weights frozen)

Identical method to the LiteParse add, generalized in `scripts/splice_vendor.py` (now per-vendor
suffix + `pre_<vendor>_archive`): `mistral` added to `build_vendor_md.VENDORS`; all four judges
re-run **10-up** to fresh `_mistral` outputs/caches with **`LA_DPT2=1`** (canonical LA slot = DPT-2)
and the canonical content `FT_*_CAP=16000`; figure eval re-judged 10-up (`FIG_VENDORS=…,mistral`).
**Validation = the existing 9 vendors' aggregate fair-total, under *canonical* weights, must be
stable between the canonical run and the 10-vendor run.** Only Mistral's column is spliced into
canonical; the other 9 stay byte-identical (originals → `results/pre_mistral_archive/`).

**Validation passed on all four passes** (worst aggregate drift on the untouched 9):

| Judge pass | worst drift | gate |
|---|---:|---:|
| gpt-5 structure (headline) | 1.41 pp | 1.5 |
| gemini structure | 1.09 pp | 1.5 |
| gpt-5 content | 1.12 pp | 1.5 |
| gemini content | 0.85 pp | 1.5 |

Figure eval re-judged 10-up to a fresh cache; the 9 stable within figure-judge noise (vision tools
<1.6pp; landingai graph −4.0 on its small graph-page n, consistent with the LiteParse add), Mistral's
column spliced into `_figure_judging.json`.

## Results

**Fair total (canonical-weighted):**

| Judge | Mistral | unsupported | rank among real vendors |
|---|---:|---:|---|
| **gpt-5 structure (HEADLINE)** | **80%** | **19%** | 5th (just below the four-vendor 86–89 cluster, +12 over PyMuPDF) |
| gemini structure | 91% | 7% | mid vision tier |
| gpt-5 content (diagnostic) | 84% | 19% | — |
| gemini content (diagnostic) | 93% | 7% | — |

**Per-category (gpt-5 structure):**

| | Text | Table | Chart | Mixed | Cover | Image |
|---|---:|---:|---:|---:|---:|---:|
| Mistral OCR 4 | **96** | 85 | 62 | 87 | 61 | **86** |
| (Gemini Flash, ref) | 95 | 87 | 84 | 93 | 84 | 82 |
| (PyMuPDF, ref) | 80 | 71 | 54 | 79 | 51 | 28 |

**Per-doc (gpt-5 structure):** Alpha (French consulting) 75 · IAR (annual report) 91 · SOTER (chart-
heavy M&A memo) 64 — best on the annual report, weakest on the chart memo, the same genre shape as
every vendor.

**Figure dims:** graph-data **59** · diagram-structure **60** — a genuine figure reader (text-layer
tools score 12–29), but the **least reliable of the vision tier** (Gemini/gpt-5 ~85, Landing AI 80).

**Objective / capability dims:** content 96% · numbers 94% · table-presence **94%** (HTML inlining) ·
exact bounding boxes · ~$3 (599pp, $5/1k Document-AI tier) · 5.2 s/pg.

## The finding

**Mistral OCR 4 is a strong text/table extractor and a real-but-unreliable figure reader, and it is
the only vendor whose error mode is *fabrication* rather than omission or structure-loss.**

1. **It enters the vision tier (80% gpt-5 structure), 5th among real vendors.** Structure gap is only
   −4 (84 content → 80 structure) — it *preserves* structure (HTML tables), unlike the text-layer
   tools (PyMuPDF −16, LiteParse −18). Top-tier on Text (96), Table (85), Image/Photo (86), Mixed (87),
   and the structure-aware re-benchmark of the Rogo chart claim: it does read charts (chart 62, vs
   text-layer ~33–54), just not as well as the vision leaders (78–84).

2. **Its annotation layer fabricates on graphics it can't parse — 19% unsupported, the highest of all
   10 vendors** (next is Tesseract 15%; the rest 5–11%). Audited examples on the worst pages: on SOTER
   p78 (certification logos + certificate thumbnails) it invented a generic "Start → Process → End"
   flowchart and a Portuguese document-management UI ("Certificado de Conclusão de Curso", "Meus
   Documentos") — content that simply is not on the page. The strict gpt-5 structure judge prices this
   as active error (19% unsupported); the more lenient Gemini judge largely misses it (7%) — which is
   itself why this benchmark scores both families. Confidently-wrong output a downstream financial user
   would not catch is worse than a visible omission.

3. **Chart 62 / Cover 61 are the soft spots.** Charts because partial chart-data recovery comes mixed
   with invented values; Cover/Divider because the annotation layer over-describes near-empty pages
   (manufacturing detail where there is none) — the same fabrication tendency from the low-information
   end.

**Verdict:** a fast-to-adopt, genuinely multi-capability vision parser — excellent on text and tables,
a real (if second-tier) chart reader, at ~$3/599pp. But the advanced annotation layer that buys its
figure reach also makes it **the most hallucination-prone vendor in the set**, so for finance use it
needs the confidence scores surfaced and a human/verification gate on figure-derived claims. For
structure-aware capture without the fabrication tax, the 86–89 cluster (Gemini Flash, Landing AI,
LlamaParse-agentic, Flash-Lite) remains ahead. This is a real capability result, consistent across
both judge families and confirmed by transcript audit — not a measurement artifact.

## Artifacts

- Shared reducer `scripts/mistral_common.py` (client, OCR call, `reduce_page`, `ImageAnnotation`
  schema); runner `scripts/mistral_run.py`; collector `collect_mistral()` in `collect_extractions.py`.
- Input A/B `scripts/ab_mistral_input.py` + `scripts/ab_score_mistral_input.py`
  (`results/_ab_mistral_input_judging.json`, `ground_truth/mistral_ab/`).
- Add-splicer `scripts/splice_vendor.py mistral` (generalized to per-vendor suffix / archive dir).
- 10-vendor judge outputs: `results/_fair_total_judging{,_gemini_v2,_content,_gemini_v2_content}_mistral.json`,
  `results/_figure_judging_mistral.json`; canonical originals in `results/pre_mistral_archive/`.
- Total judge cost **~$48** (gpt-5 structure $13.83 + content $13.95; Gemini structure $7.9 + content
  $8.40; figure $4.18) + ~$3 parsing + ~$0.6 A/B. Cleanly comparable to the LiteParse add.
- Regenerated: `results/FAIR_TOTAL.md`, `results/BY_DOCUMENT.md`, `results/EXTRACTION_COMPARISON.md`;
  prose synced in `README.md`, `FINAL_REPORT.md`, `DESIGN.md`.
- **Not run:** element-level eval (6129 typed elements) — out of scope, as it was for LiteParse and the
  DPT-2 re-bench; OCR 4's capability is well-characterized by the fair-total + figure + objective dims.
