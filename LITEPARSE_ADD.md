# Adding LiteParse (run-llama OSS) as the 9th vendor

*2026-06-23. Full-corpus benchmark of LiteParse, validated and spliced into the canonical fair-total
(both judge families, structure-aware + content) and the figure eval. Headline: **62% structure-aware
— below PyMuPDF (68%), above Tesseract (52%)**.*

## What LiteParse is

[LiteParse](https://github.com/run-llama/liteparse) (run-llama, Apache-2.0, released ~May 2026) is
the **open-sourced core of LlamaParse with the VLM layer removed** — a local, CPU-only document
parser. Pipeline: PDFium native text extraction → an anchor-based **"grid projection"** (`SnapKind`
left/right/center column detection → snap text onto a character grid that mirrors the visual layout)
→ heuristic, rule-based **markdown** (pipe tables, headings, lists). Tesseract OCR auto-triggers only
when a page's native text layer is sparse. It is **vision-blind** — no chart/diagram understanding —
which is exactly why run-llama route "the hardest documents (dense tables, multi-column, scans,
charts)" to the paid LlamaParse. This benchmark tests whether its spatial markdown beats a plain
PyMuPDF text dump on real finance/M&A/consulting documents.

## How it was run (free, local)

- `pip install liteparse` (v2.1.1, prebuilt arm64 wheel) into `.venv-liteparse`.
- **Input = the born-digital PDF** (`Data/*.pdf`), LiteParse's native input — the same text layer
  PyMuPDF reads via fitz. Forcing the PNG renders (as the vision vendors need) would handicap it into
  pure OCR, which is already covered by the Tesseract vendor. Consistent with the project's
  "best/native input per tool" principle.
- **Representation = per-page reconstructed markdown** (`result.text` on a single-page parse) —
  LiteParse's flagship output and best foot forward, the direct analogue of LlamaParse's page-`md`
  path. The whole-document markdown has no page delimiters, so pages are parsed individually.
- `scripts/liteparse_run.py` → resumable per-page cache `ground_truth/liteparse/raw/{doc}__p{page}.md`.
  599 pages in **789 s (~1.3 s/page)**, **0 errors**, and only **~1 page** flagged sparse-text/
  OCR-candidate — confirming the corpus is born-digital and OCR essentially never fired (clean
  text-layer comparison, no Tesseract-quality confound).
- `collect_liteparse()` in `collect_extractions.py`: strips empty image placeholders (`![](…)` —
  vision-blind, no description), serves the whole page md as the single ordered block (→
  `ordered_full` = the md, like the LlamaParse page-md path), extracts pipe-table blocks into
  `tables` (452 across the corpus, vs PyMuPDF's ~43%), `figures=[]`. → `results/_extract_liteparse.json`.

## How it was judged (add, not swap — weights frozen)

`splice_dpt2.py` handled a *swap* (legacy LA → DPT-2, same 8 vendors). Adding a 9th vendor changes the
judge prompt (9 extractions, fresh weights), so `scripts/splice_vendor.py` generalizes the method for
an **add**:

1. `liteparse` added to `VENDORS` (`build_vendor_md.py`); all four judges re-run **9-up** to fresh
   `_lp` outputs/caches, with **`LA_DPT2=1`** so the `landingai` slot matches canonical (DPT-2 was
   spliced in). Content runs used the canonical `FT_*_CAP=16000`.
2. **Validation = the existing 8 vendors' aggregate fair-total, computed under *canonical* weights,
   must be stable** between the canonical run and the 9-vendor run (per-page judge variance ±20-25pp
   is noise and averages out; only the weighted aggregate must hold — same gate as the DPT-2 splice).
3. The 9-vendor run's re-rolled weights are **discarded**; only LiteParse's recall/unsupported column
   is spliced into canonical, keeping canonical weights and the other 8 byte-identical (originals →
   `results/pre_liteparse_archive/`).

**Validation passed on all four passes** (worst aggregate drift on the untouched 8):

| Judge pass | worst drift | gate |
|---|---:|---:|
| gpt-5 structure (headline) | 1.34 pp | 1.5 |
| gemini structure | 0.81 pp | 1.5 |
| gpt-5 content | 0.98 pp | 1.5 |
| gemini content | 0.73 pp | 1.5 |

`landingai` was stable in every pass (e.g. 86.0→86.5 gpt-5 structure), confirming the `LA_DPT2=1`
control. Figure eval re-judged 9-up to a fresh cache (`figure_judge_lp`), the 8 stable within
figure-judge noise (structure-preservers <1.6 pp; PyMuPDF/Tesseract 2–4 pp, expected on their small
graph-page n), LiteParse's column spliced into `_figure_judging.json`.

## Results

**Fair total (canonical-weighted):**

| Judge | LiteParse | unsupported | PyMuPDF (ref) | Tesseract (ref) |
|---|---:|---:|---:|---:|
| **gpt-5 structure (HEADLINE)** | **62%** | 9% | 68% | 52% |
| gemini structure | 65% | 13% | 68% | 67% |
| gpt-5 content (diagnostic) | 80% | 5% | 84% | 64% |
| gemini content (diagnostic) | 80% | 4% | 84% | 77% |

**Per-doc (gpt-5 structure):** Alpha (French consulting) 55 · IAR (annual report) 72 · SOTER (M&A
memo) 51 — same genre shape as PyMuPDF (best on the annual report, worst on the chart memo), a few
points lower everywhere.

**Per-category fair-total (gpt-5 structure) vs PyMuPDF:**

| | Text | Table | Chart | Mixed | Cover | Image |
|---|---:|---:|---:|---:|---:|---:|
| LiteParse | **85** | 60 | 44 | 71 | 50 | **54** |
| PyMuPDF | 80 | **71** | **54** | **79** | 51 | 28 |

**Objective / capability dims:** content 96% · numbers 95% · table-presence **81%** (PyMuPDF 57%,
Tesseract 0%) · graph-data **12%** · diagram-structure **14%** · exact element bounding boxes · $0 local.

## The finding

**LiteParse scores *below* PyMuPDF (62 vs 68) despite being the OSS core of LlamaParse, and is the
worst figure reader of all nine vendors.** The story is consistent across both judge families and
every diagnostic:

1. **It is vision-blind**, so on figures it scores 12/14 (graph/diagram) — *below even PyMuPDF's
   29/29 flat dump*, because its grid projection **scatters/merges** the raw chart numbers that a
   plain dump preserves verbatim, and it captures fewer chart-as-table cases than fitz's table finder.
2. **Its markdown reconstruction helps on prose, hurts on structured data.** It emits far more
   table/heading *shape* than PyMuPDF (table-presence 81% vs 57%) and **beats PyMuPDF on plain text
   (85 vs 80) and image/photo (54 vs 28)** — but on dense multi-column finance pages the grid
   projection **merges adjacent columns into a jumble whose row/column bindings are unrecoverable**,
   so the table-shaped output earns *no* structure credit and it **loses on every structured
   category** (Table 60 vs 71, Chart 44 vs 54, Mixed 71 vs 79). Example: IAR p258 — it interleaves an
   EPS table's cells with adjacent segment prose; SOTER p90 — it produces a clean pipe table where
   PyMuPDF dumps a flat number list. The grid helps on simple slides, breaks on hard finance pages.
3. **Largest structure gap of any vendor (−18):** content 80 → structure 62. It captures the
   characters but loses the most structure relative to what it captured — the binding penalty shows up
   as *unrecoverable* (low recall), not *wrong* (its unsupported is a moderate 9%).

**Verdict:** a fast, local, permissively-licensed (Apache-2.0) **text-and-prose first pass** — and a
genuinely free alternative to AGPL PyMuPDF for that use — but **not a structured-data extractor**. For
finance tables/charts, PyMuPDF+fitz's native table finder is the stronger free baseline and any vision
tool (Gemini Flash, Landing AI, agentic LlamaParse) is a tier above. This is a real capability result,
not a measurement artifact.

## Artifacts

- Runner `scripts/liteparse_run.py`; collector `collect_liteparse()` in `scripts/collect_extractions.py`.
- Add-splicer `scripts/splice_vendor.py` (generalizes `splice_dpt2.py` to an add).
- 9-vendor judge outputs: `results/_fair_total_judging{,_gemini_v2,_content,_gemini_v2_content}_lp.json`,
  `results/_figure_judging_lp.json`; canonical originals in `results/pre_liteparse_archive/`.
- Total judge cost **$45.16** (gpt-5 structure $12.85 + content $12.86; Gemini structure $7.91 +
  content $7.63; figure $3.91). Parsing + objective dims free/local.
- Regenerated: `results/FAIR_TOTAL.md`, `results/BY_DOCUMENT.md`, `results/EXTRACTION_COMPARISON.md`;
  prose synced in `README.md`, `FINAL_REPORT.md`, `DESIGN.md`.
- **Not run:** element-level eval (6129 typed elements) — out of scope, as it was for the DPT-2
  re-bench; LiteParse's capability is well-characterized by the fair-total + figure + objective dims.
