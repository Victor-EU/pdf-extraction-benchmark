# PDF Extraction Benchmark — Design & Methodology

> **Metric update (2026-06-14): the headline fair total is now STRUCTURE-AWARE.** A value is
> credited only if its binding (row/column/series/node) is recoverable, and an actively wrong
> binding counts as a contradiction — because on this corpus a number bound to the wrong row is an
> active downstream error. Content recall (the prior rubric) is retained as a diagnostic. Full
> definition, both-judge-family results, and validation: [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md).

**Status:** locked · **Last updated:** 2026-06-13
**Corpus:** 3 real-world finance/business PDFs · 599 pages
**Companion document:** [`FINAL_REPORT.md`](FINAL_REPORT.md) (results & recommendations)

---

## 1. The question

> *Given a complex, real-world business PDF, which extraction approach recovers the most of the document's actual information — not just its words, but its tables, charts, diagrams, and layout?*

This is deliberately broader than "OCR accuracy" or "table F1." A modern finance or strategy document is a **multi-modal artifact**: a single page may carry a paragraph of narrative, a 20-row financial table, a label-free bar chart, an org-chart diagram, and a photo — each holding information a downstream reader (or an LLM agent) needs. A parser that nails the text but drops the chart data has failed the document, even at "97% token recall."

So the benchmark measures **information capture across five capabilities**:

1. **Text** — verbatim narrative and labels
2. **Tables** — structured cells, including numeric/financial data
3. **Charts/graphs** — the underlying *data values*, not just "a chart exists"
4. **Diagrams** — nodes, relationships, hierarchy (org charts, process flows, schematics)
5. **Layout** — reading order and (where applicable) element coordinates

And it answers the question at two resolutions: **per-capability** (the diagnostic matrix) and **whole-document** (the single "fair total" — how much of the entire 599-page document each vendor conveyed).

---

## 2. The corpus

Three PDFs were chosen to span document *genres*, *languages*, and *content mixes* that a finance/analyst workflow actually encounters. All three are **born-digital** (clean embedded text layer) — a property that matters for interpreting the results (§8).

| Document | Pages | Genre | Language | Character |
|---|---:|---|---|---|
| `20190308_Projet_Alpha_Restitution` | 156 | Strategy consulting deck (Roland Berger / Parc Oméga) | French | Dense tables, org charts, photo-grids, sensitivity dials |
| `IAR_FY25_EN` | 310 | Integrated Annual Report (eDreams ODIGEO FY25) | English | Financial statements, ESG risk tables, long-form narrative, governance diagrams |
| `SOTER - Company Presentation - vFF` | 133 | Investor presentation (AddSecure / Arma Partners) | English | **Label-free** charts (ARPU, MRR, subscriber bridges), dashboards, infographics |

**Why this mix is a good test:** the consulting deck stresses multilingual text + diagrams; the annual report stresses dense financial tables and verbatim prose at scale; the investor deck stresses the hardest case of all — **charts with no printed data labels**, where any extractor must *read the geometry* of bars and lines. Together they exercise every capability the benchmark scores.

### Page-category distribution (v3 answer key, 599 pages)

| Category | Pages | Share |
|---|---:|---:|
| Chart/Diagram | 152 | 25% |
| Text | 149 | 25% |
| Table | 128 | 21% |
| Mixed | 113 | 19% |
| Cover/Divider | 55 | 9% |
| Image/Photo | 2 | 0.3% |

> **Image/Photo is tiny by design.** A page that is *functionally* a section cover — even if it's a full-bleed photograph — is labeled **Cover/Divider by function**, not Image/Photo. Only pages whose *purpose* is to present a photograph as content count as Image/Photo. This is a rubric convention, not an oversight (see `ground_truth/RUBRIC.md`).

---

## 3. The two-layer ground truth

The methodological core of this benchmark is that it has **two independent ground-truth layers**, built for two different jobs, and that the more debatable layer was **independently validated by a third model family**.

### Layer 1 — Category answer key (what *kind* of page is this?)

`ground_truth/reconcile/final_answer_key_v3.json` — one of six mutually exclusive labels per page. Built from **two intelligent sources plus deep-think adjudication**, never a single model's opinion:

1. **Claude vision** labels every page against the locked rubric (calibrated subagents). → `ground_truth/vision_full/`
2. **Landing AI ADE** parses every page; its typed chunks are reduced to a dominant label. → `ground_truth/landingai_full/`
3. **Reconcile.** The two sources **agree on 365/599 pages (61%)** → locked immediately. The **234 disagreements** go to per-page **deep-think adjudication** (a fresh re-examination of the page image holding both opinions), then **manual review** of the 7 still-uncertain / both-overridden cases.
   - Tie-break outcome: vision won 198, Landing AI won 30, the adjudicator overrode both on 6, and 3 more changed on final manual review.
   - A deterministic PyMuPDF heuristic was prototyped as a third source but **dropped** (only 32% agreement — too weak to adjudicate). Its features survive only as throwaway diagnostics.

**Job of Layer 1:** to *segment* the extraction scoring by content type ("how does each vendor do **on the table pages** vs **the chart pages**"). It is **not** used to rank the parsers on classification — that would be circular, because Claude and Landing AI co-authored it. The circularity is contained: the key slices the harder extraction metrics; it never scores the two models that built it against each other.

### Layer 2 — `GROUND_TRUTH.md` (what *information* is on this page?)

`ground_truth/GROUND_TRUTH.md` — a faithful, free-form **markdown transcription of all 599 pages**, in reading order. This is the reference the **fair total** diffs against.

- **Built by:** gpt-5 vision (`build_gt_md.py`), reasoning effort = **medium**, one page at a time, resumable per-page cache.
- **Prompt design:** transcribe text **verbatim**; render tables as markdown tables with every cell; describe charts as `**Chart:**` with axis labels, series names, and **data values** (estimated with a `~` prefix where the source prints no labels); describe diagrams as `**Diagram:**` with nodes and relationships; describe photos/logos as `**Image:**`/`**Logo:**`.
- **Scale & cost:** 599 pages, **1,502,226 characters**, 662k input / **2.13M output** tokens, **$22.18**, **0 empty pages**.

**Why a separate transcription layer at all?** Because the per-capability metrics (Layer-1-sliced token recall) **saturated** — every serious vendor scored 95–97% content recall — and token overlap *unfairly penalizes correct paraphrase* (a diagram described in different-but-equally-correct words scores low on lexical overlap). To measure *information* rather than *wording*, you need a complete reference of the information itself, plus a judge that credits equivalent phrasing (§5, Gen 3).

### Independent validation & correction of Layer 2 (the twin-bias firewall)

`GROUND_TRUTH.md` is built by gpt-5 **and** scored by a gpt-5 judge (§5). That co-location is the single most dangerous failure mode in the whole design: a **shared blind spot** could silently corrupt every downstream number. We attacked it on three axes and — importantly — **found real defects, corrected them, and re-measured** (full account: [`GT_VALIDATION.md`](GT_VALIDATION.md)).

- **Faithfulness audit (Claude, independent family):** a **36-page chart-weighted** sample (3.4× a first 16-page pass), every flag re-verified by hand at high zoom → **30 faithful, 2 minor, 4 material defects, all on dense multi-series figures** (e.g. SOTER p30: 17/21 *printed* ARPU labels replaced by a smoother invented series). The financial-statement pages are model-independently sound — IAR p258/p265 foot internally and tie cross-page (profit-before-tax **48,937** on both). An earlier "16/16" spot-check simply had not sampled the hard figure pages.
- **Scope via the text layer:** because the corpus is born-digital, every printed number is an exact oracle. A 599-page text-layer diff put v1 printed-number fidelity at 97.5% on charts / 98.4% overall, and showed the figure errors **biased the benchmark *against* the text-layer parsers** (they were penalised for disagreeing with gpt-5's hallucinated values).
- **Correction (`build_gt_md_v2.py`):** all 275 figure pages rebuilt with the **authoritative text layer + a 2400px render** (vs the original 1600px), gpt-5 kept as builder so it stays ◆. Printed-number fidelity → 99.1% charts / 99.5% overall; every audited defect fixed. This corrected reference is now canonical (v1 archived `GROUND_TRUTH_v1.md`).
- **Re-measure:** with only the reference changed, the **ranking is identical**; the text-layer parsers gained most on charts (PyMuPDF +7.6, LlamaParse +6.4) while gpt-5-image — sharing the GT's blind spot — was the only vendor that did not improve (−0.2). A **non-OpenAI (Gemini) judge** reproduces the top-four ranking. The twin bias was real, is removed, and did not change the conclusions.

*(Distinct from `results/GROUND_TRUTH_AUDIT.md`, which audits **Layer 1** — the category key — using gpt-5 as an independent third vote and finds it sound.)*

---

## 4. The eleven approaches under test

Three architectural families, eleven configurations. Each produces a normalized per-page record (`scripts/collect_extractions.py` → `results/_extract_<vendor>.json`) and a full reconstructed document (`scripts/build_vendor_md.py` → `results/vendor_md/<vendor>.md`).

| # | Vendor / config | Family | How it sees the page | Coordinates |
|---|---|---|---|---|
| 1 | **gpt-5 (image)** | Native-vision LLM | Rendered PNG → block schema | coarse |
| 2 | **gpt-5 (file)** | Native-vision LLM | Native PDF upload → block schema | coarse |
| 3 | **Gemini 3.5 Flash** | Native-vision LLM | Rendered PNG, *identical* prompt+schema to gpt-5 | coarse |
| 4 | **Gemini 3.1 Flash-Lite** | Native-vision LLM | Rendered PNG, identical prompt+schema | coarse |
| 5 | **Landing AI ADE** | Specialized doc parser | Typed-chunk layout model | **exact boxes** |
| 6 | **LlamaParse** (agentic tier) | Specialized doc parser (LVM agent loop) | Layout + table + figure-reading model | **exact boxes** |
| 7 | **PyMuPDF** | Classical text-layer | Embedded text + `find_tables()` | **exact boxes** |
| 8 | **Tesseract** | Classical OCR | Full-page OCR on rasterized pages | word boxes |
| 9 | **LiteParse** (run-llama OSS) | Classical text-layer + spatial grid | PDFium text → anchor grid-projection → heuristic markdown (auto-OCR on sparse pages) | **exact boxes** |
| 10 | **Mistral OCR 4** (`mistral-ocr-4-0` + Document-AI annotations, most advanced config) | Specialized doc parser (OCR + per-image VLM annotation) | Rendered PNG → markdown + figure-describing annotation layer (input A/B'd; PNG won — `MISTRAL_ADD.md`) | **exact boxes** |
| 11 | **Pulse** (Ultra 2 + `refine` + figure description, most advanced config) | Specialized doc parser (OCR + `refine` re-OCR pass) | Rendered PNG per page → markdown, chart/diagram prose woven inline (`PULSE_ADD.md`) | **exact boxes** |

**Controls baked into the line-up:**
- **gpt-5 image vs file** isolates *render-PNG vs native-PDF* input for the same model.
- **Gemini runs the byte-identical prompt + schema as gpt-5**, in image mode, so the gpt-5↔Gemini gap isolates *the model*, not the harness. (`thinkingLevel=minimal` ≈ gpt-5 `effort=low`.)
- **PyMuPDF, LiteParse and Tesseract are the zero-*usage*-cost local floor** — the value question is "how much does paying buy you over a born-digital text dump / spatial-grid markdown / plain OCR?" (License: **Tesseract is Apache-2.0** and **LiteParse is Apache-2.0** — both truly free, including proprietary/SaaS; **PyMuPDF is AGPL-3.0 or a paid Artifex commercial license** — $0 to *run* but *not* free for proprietary/SaaS deployment, where pdfplumber (MIT) / pypdf (BSD) / LiteParse are the permissive equivalents. See `FINAL_REPORT.md` §6 note ¹.) **LiteParse is the open-sourced core of LlamaParse minus the VLM** — included to test whether its spatial "grid-projection" markdown beats a plain PyMuPDF text dump (it does on prose, *not* on structured finance data — see `LITEPARSE_ADD.md`).
- **Landing AI, LlamaParse, Mistral OCR 4 and Pulse are the specialized parsers** — the tier that emits exact element coordinates, which no LLM does. Mistral and Pulse (added 2026-06-23 / 2026-06-30) are each run in their most advanced documented config, per the tier lesson from the LlamaParse audit; they also bracket the fidelity axis — Mistral is the fabrication outlier (19% unsupported), Pulse the cleanest vision vendor (5%).

---

## 5. Three generations of metric (and why each exists)

The scoring evolved as earlier metrics were found to either **saturate** or **mislead**. All three generations are preserved; the fair total is the headline.

### Gen 1 — Category classification accuracy
`scripts/score_solution.py` scores a vendor's *page labels* against Layer 1 (overall accuracy, per-category P/R/F1, confusion matrix, speed, cost). Useful as a routing/triage signal. **Circular for Claude & Landing AI** (they built the key), so it is reported for *other* solutions only and is not the headline.

### Gen 2 — Per-capability extraction quality
`scripts/score_extraction.py` + figure judging. Two metric sub-families, both sliced by Layer-1 category:

- **Objective recall**, scored against a **vendor-neutral reference** = (born-digital text-layer) ∪ (image-region OCR), *not* any vendor's output:
  - **Content-token recall**, **numeric/finance recall**, **table recovery**, **reading order** (Kendall-τ).
- **Figure judging** — a **blind gpt-5 vision judge** grades against the *page image* (not against a vendor), all 10 extractions shuffled A–J (Pulse is excluded from this structured figure judge — it emits no figure blocks; its figure reading is scored by the Chart category of the fair total instead; see [`PULSE_ADD.md`](PULSE_ADD.md)):
  - **graph-data fidelity** over the 123 graph pages, **diagram-structure fidelity** over the 97 diagram pages.

> **The `table_recovery` correction (the original spark for this audit).** The first table metric scored Landing AI at **56%**, which looked wrong. Two bugs were found and fixed:
> 1. **Collector bug** — Landing AI's ADE classifies a table embedded with a logo/photo/icon as a `figure` chunk whose text holds the *full table*; the collector only counted literal `table` chunks, silently discarding those. Fixed by detecting figure-embedded tables (`_la_figure_is_table`: requires the word "table" **and** structural evidence — bullets/pipes/digits).
> 2. **Denominator bug** — the metric required a table on every `Table`∪`Mixed` page, but ~half of `Mixed` pages are chart+text with **no table**; demanding one punished principled abstention (Landing AI) and rewarded over-emission (the accurate-tier LlamaParse emitted a table on every no-table Mixed page checked; the agentic tier instead tabulates real chart data). Fixed by scoring **only the 128 `Table`-labeled pages**.
>
> Corrected, Landing AI's table recovery is **91%**, not 56%. The old value survives as `table_presence_legacy` in `_extraction_objective.json`. *This was a metric artifact, not a ground-truth error.* A tree-wide collector audit confirmed **no analogous bug** in the other vendors.

**Why Gen 2 wasn't enough:** content recall saturated at 95–97% for every serious vendor (a ~2pp spread that can't discriminate), and "averaging the dimensions" requires arbitrary weights. A document is not the mean of six scores.

### Gen 3 — The fair total (the headline)
`scripts/score_fair_total.py` + `scripts/fair_total_report.py`. A **document-level, paraphrase-tolerant, density-weighted** measure of *how much of the document's real information each vendor conveyed*.

- **Unit of judgment:** the page. For each of the 599 pages, a **blind gpt-5 judge** sees the `GROUND_TRUTH.md` page plus **all 11 vendors' full page markdown, shuffled A–K**, and returns, per vendor:
  - `info_recall` (0–100): what fraction of the GT's substantive information (facts, numbers, table cells, **chart data values**, diagram nodes/relationships, labels) the extraction conveys. **Equivalent phrasing is credited as fully correct** — a chart described in different-but-correct words with the same numbers scores full marks. Information is rewarded, not verbosity or wording.
  - `unsupported` (0–100): the fidelity flag — what fraction of the extraction's claims **contradict** the GT or assert **wrong/invented** facts. *Crucially, this counts only genuine errors* — a fuller-but-consistent description is **not** penalized. (This definition was tightened after a v1 smoke test over-penalized Landing AI's verbose figure prose as "unsupported"; see §6.)
  - `page_info_weight` (1–10): how much real information the page holds (1 = a divider/title; 10 = a dense data table or multi-series chart).

- **The headline number:**

  $$\text{Fair total} = \frac{\sum_{\text{pages}} \text{info\_recall} \times \text{page\_info\_weight}}{\sum_{\text{pages}} \text{page\_info\_weight}}$$

  This is a **true ratio of total information captured to total information present**, weighted by how much each page actually holds — a dense financial table counts far more than a section divider. It is explicitly **not** an average of arbitrary dimension scores, and **not** lexical token overlap.

- **Cost & integrity:** 599 pages, reasoning effort = low, **$12.67**, **0 errors**. Caches per page (`ground_truth/fair_total_judge/`).

---

## 6. Bias controls (why the numbers can be trusted)

This benchmark uses an LLM as both transcriber and judge, so it is built around an explicit set of controls. Each addresses a specific threat:

| Threat | Control |
|---|---|
| Judge favors a *recognizable* vendor | **Blind judging** — all extractions shuffled to letters per page (A–K on the headline fair total, A–J on the figure judge); the judge never learns whose is whose. |
| Judge grades against a vendor's style | **vs-image / vs-GT** — the figure judge grades against the *page image*; the fair-total judge against the *transcription*. Neither grades against a vendor output. |
| Lexical overlap punishes correct paraphrase | **Paraphrase credited** — equivalent phrasing with the same facts/numbers scores full `info_recall`. |
| Verbosity mistaken for error | **`unsupported` = contradictions only** — fuller-but-consistent descriptions are not penalized (tightened after a v1 smoke test flagged Landing AI's long figure prose; LA's `unsupported` dropped from 80→10 on re-validation, confirming the original flag was a verbosity artifact). |
| **gpt-5 transcribes AND gpt-5 judges (twin bias)** | (a) gpt-5's own rows flagged **◆ upper-bound, not comparable**; (b) against the corrected GT **Gemini Flash *edges* gpt-5 (92% vs 91%)** despite the twin advantage → the residual bias is mild; (c) on figure judging, gpt-5 scored **Gemini's diagrams *above its own*** (91% vs 66%) blind, and a **non-OpenAI Gemini judge** keeps the same top-four set with Gemini Flash #1 (Landing AI and Flash-Lite trade 2nd/3rd) — neither judge favours its own family; (d) the independent audit **plus the text-layer correction** of the GT (§3) removes the more dangerous failure — a *corrupt* reference — and the demonstration that the figure errors biased *against* the parsers, not toward the LLMs. |
| Reference flatters a vendor | **Neutral objective reference** = text-layer ∪ OCR, not a vendor output. **Known caveat:** PyMuPDF's reading-order score is inflated because the reference uses the same layout engine — it is flagged as a capability indicator, not a ranking. |
| Demanding a table where none exists | **Abstention fairness** — table recovery scores only true `Table` pages; `Mixed` excluded. |
| **Judge-input truncation penalises the most verbose vendor** | A per-page character cap on the text shown to the judge clipped only **Landing AI** (2× longest output). Audited across all three judge harnesses, re-judged at **no-truncation caps** under both judge families: Landing AI rose 2–13pt on the affected dimensions, **no ranking changed**. Full trail: [`AUDIT_VEND_CAP.md`](AUDIT_VEND_CAP.md). |
| **The judge could silently corrupt the numbers (it built and grades the GT)** | **Deterministic oracle cross-check** — a zero-LLM, zero-variance binding-aware validator (`scripts/deterministic_validate.py`) independently reproduces the table-page structure tiering and the text-dumper collapse *without invoking the judged model*, reports an oracle-backed numeric-fidelity floor, and flags vendor-specific judge↔oracle disagreements for review (it has already caught a harness bug and a Landing AI column-shift the judge correctly penalised). Scoped to numeric bindings on born-digital pages — blind to charts/diagrams by construction. [`DETERMINISTIC_VALIDATION.md`](results/DETERMINISTIC_VALIDATION.md), [`POC_DETERMINISTIC_SCORING.md`](POC_DETERMINISTIC_SCORING.md). |

A residual **robustness** data point, not a bias artifact: each Gemini model hit the shared 16k-output cap via runaway repetition on **exactly one page** (`gemini-3.5-flash`: Alpha p5; `gemini-3.1-flash-lite`: IAR p103), scoring those empty. 1/599 each; aggregates unaffected; gpt-5 did both pages in ~2k tokens.

---

## 7. Reproducibility

### Pipeline order
```
render_all.py                  # PDFs → 599 page PNGs (1600px cap) + manifest
─ Layer 1 (category key) ─
  vision (Claude subagents) ─┐
  landingai_pass.py          ├─ reconcile_full.py → deep-think → manual → final_answer_key_v3.json
─ Layer 2 (transcription) ─
  build_gt_md.py             # gpt-5 vision → GROUND_TRUTH.md  ($22.18)
─ Vendor extractions ─
  openai_extract.py (image|file)        gemini_extract.py (flash|flash_lite)
  landingai_pass.py   llamaparse_fetch.py   pymupdf_parser.py   tesseract_parser.py
  collect_extractions.py <vendor>        # → results/_extract_<vendor>.json
  build_vendor_md.py                     # → results/vendor_md/<vendor>.md
─ Scoring ─
  score_extraction.py + score_figures.py → extraction_report.py → EXTRACTION_COMPARISON.md   (Gen 2)
  score_fair_total.py → fair_total_report.py → FAIR_TOTAL.md                                  (Gen 3)
  score_solution.py                                                                           (Gen 1)
```

### Conventions & gotchas
- **Caches everywhere** — every model call writes a per-page JSON cache (`ground_truth/*/`), so re-runs are free and resumable.
- **Landing AI SSL** requires the `requests` + `certifi` pattern (the SDK's default SSL context fails in this environment).
- **API keys** live only in a gitignored `.env` (`OPENAI_API_KEY`, `GEMINI_API_KEY`) — never hardcoded or committed.
- **OpenAI calls** use the Responses API (`client.responses.create`, `reasoning={"effort"}`, `text={"format": json_schema strict}`).

---

## 8. Limitations & threats to validity

Stated plainly, because a benchmark is only as honest as its caveats:

1. **All three PDFs are born-digital.** Every page has a clean embedded text layer. This **flatters PyMuPDF** (perfect text from the layer, at $0 usage — though PyMuPDF is AGPL-licensed, not free for proprietary use; see `FINAL_REPORT.md` §6 note ¹) and compresses the objective content-recall spread to ~2pp. On **scanned or photographed** documents the text-layer floor collapses and the vision LLMs / OCR parsers would separate far more. The fair total is more robust to this (it judges *information*, not text-layer presence), but the corpus is not a scanned-document test.
2. **gpt-5 is both transcriber and judge.** Mitigated four ways (§6) and the gpt-5 rows are flagged ◆ upper-bound — but they are reported, not ranked. Gemini and the field below it are graded cleanly.
3. **Chart data values are inherently estimated.** Label-free bars/lines have no ground-truth numbers; the GT records `~`-estimates and the judge credits any consistent reading. This is the right call for unlabeled charts, but chart-data scores carry more irreducible uncertainty than table scores.
4. **Single judge pass.** The fair total is one gpt-5 judgment per page, not a panel vote. Blind shuffling + paraphrase tolerance + the contradiction-only fidelity definition make it stable, but it is not a multi-judge consensus.
5. **n = 3 documents.** Diverse and large (599 pages) but three documents; vendor rankings are most trustworthy where the gaps are wide (e.g. Tesseract's figure collapse), least where they are within a few points.
6a. **Vendor tier/mode matters as much as vendor choice.** LlamaParse was first benchmarked in its middle `accurate` tier and scored 71%; its most capable `agentic` tier scores 90% (a +19pp swing that changed its rank from last to 3rd). Always benchmark each vendor's most capable documented mode. See `AUDIT_LLAMAPARSE_MODE.md`.
6. **Cost figures are point-in-time** vendor pricing on this corpus; Landing AI's per-page rate was not captured as a dollar figure (`paid`).

---

## 9. Artifact map

| Artifact | What it is |
|---|---|
| `Data/*.pdf` | the 3 source documents |
| `ground_truth/RUBRIC.md` | locked 6-category rubric |
| `ground_truth/reconcile/final_answer_key_v3.json` | Layer 1 — authoritative category key |
| `ground_truth/GROUND_TRUTH.md` | Layer 2 — 599-page transcription reference |
| `results/_extract_<vendor>.json` | normalized per-page extraction (11 vendors) |
| `results/vendor_md/<vendor>.md` | each vendor's full reconstructed document |
| `results/EXTRACTION_COMPARISON.md` | Gen-2 per-capability matrix |
| `results/FAIR_TOTAL.md` | Gen-3 headline + per-category fair total |
| `results/GROUND_TRUTH_AUDIT.md` | Layer-1 (category key) audit — gpt-5 third-vote triangulation |
| `FINAL_REPORT.md` §9 | Layer-2 (transcription) audit — independent Claude-vision validation |
| `results/DETERMINISTIC_VALIDATION.md` | zero-LLM triangulation: table tiering + numeric floor + judge-disagreement worklist |
| `results/_deterministic_disagreements.json` | vendor-outlier judge↔oracle disagreement queue (the next-bug review list) |
| `scripts/*.py` | the full reproducible pipeline (§7) |

→ **Results, rankings, and recommendations:** [`FINAL_REPORT.md`](FINAL_REPORT.md)
