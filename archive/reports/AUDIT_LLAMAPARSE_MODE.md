# Pre-publication audit — LlamaParse was benchmarked in the wrong tier

**Date:** 2026-06-13 · Companion to [`FINAL_REPORT.md`](FINAL_REPORT.md), [`GT_VALIDATION.md`](GT_VALIDATION.md),
[`AUDIT_VEND_CAP.md`](AUDIT_VEND_CAP.md). Triggered by the question: *"LlamaParse is well-respected in
banking and our earlier audit showed great results — are we sure we used their best solution, compared it
correctly, and that the ground truth is fair?"*

## Bottom line

The original benchmark ran LlamaParse in its **`accurate`** tier — a *middle* tier — not its most
capable **`agentic`** tier. On this born-digital finance/business corpus the `accurate` tier
**catastrophically dropped whole pages** (e.g. the entire IAR auditor's-report section), which scored
~0 recall and dragged the vendor down. Re-running all 599 pages at **`agentic`** tier and re-judging
(both judge families, weights held fixed) lifts LlamaParse **+18.5 pp (gpt-5 judge) / +21.8 pp (Gemini
judge)** — moving it from **last among the parsers to 4th of 8 overall**, above Landing AI and PyMuPDF
and level with Gemini Flash-Lite. **`agentic` is now the canonical LlamaParse result.** The other seven
vendors are unchanged (≤0.7 pp, judge noise). This is the third "a measurement choice deflated one
vendor" finding in this project (after the `table_presence` artifact and the `VEND_CAP` truncation).

---

## 1. The three questions, answered

### Q1 — Were we using their most capable solution? **No — now fixed.**
- The original `scripts/llamaparse_fetch.py` uploaded each PDF with **no `parse_mode`/tier set**, so the
  job ran in the default **`accurate`** tier (confirmed: every page's `parsingMode == "accurate"`,
  `costOptimized == false`).
- The prior `pdf-extraction-audit` that "showed great results" explicitly used **`tier: agentic`**
  (confirmed in its saved job metadata) on the *identical* `IAR_FY25_EN.pdf`, scoring **87.8%** there.
- LlamaParse's banking reputation rests on the **agentic** tier (agent + LVM loop). Benchmarking the
  middle tier understated the vendor.
- **Fix:** `scripts/llamaparse_fetch_agentic.py` re-parses all three PDFs at `tier="agentic",
  version="latest"` via the official `llama_cloud_services` SDK. Raw saved to
  `ground_truth/llamaparse_agentic/raw/`.

**How bad was the `accurate` tier on this corpus?** It silently dropped whole born-digital text pages:

| IAR page (accurate tier) | accurate chars | agentic chars | content |
|---|---:|---:|---|
| p228–237 (EY auditor's report) | 161–163 each | 2,699–7,122 each | full audit-opinion body — **dropped entirely** by accurate, recovered by agentic |

The `accurate` tier returned only the running-header chrome on these pages while reporting
`confidence ≈ 0.96` and `noTextContent: false` — a *silent* failure. 6 pages on IAR were near-total
drops; 18 more lost >2× their content. Agentic produced **0 empty pages** across all 599.

### Q2 — Were the parsed data compared correctly against GT? **Yes — the plumbing is clean.**
- The judge reads each vendor's page via `page_md()` (`scripts/build_vendor_md.py`); for LlamaParse the
  record is assembled from items / the canonical page `md`. Verified the items-assembly captured **97–99%**
  of LlamaParse's own page markdown — no content lost in normalization.
- The judge saw **1.15M chars** from LlamaParse (accurate), on par with peers (Landing AI 1.20M, PyMuPDF
  1.13M, Gemini Flash 1.15M). No starvation.
- No truncation: accurate avg ~1.9K ch/page (max ~12K), agentic max 9.3K ch/page — both under the
  16,000-char judge cap fixed in `AUDIT_VEND_CAP.md`.
- The per-vendor consolidated markdown in `results/vendor_md/<vendor>.md` is **byte-faithful** to exactly
  what the judges scored (0 mismatches, asserted). These are the publishable ground-data artifacts; see
  `results/vendor_md/README.md`.
- **The accurate-tier drops were a genuine vendor-mode limitation, not a pipeline bug.**

### Q3 — Is the ground truth fair to LlamaParse? **Yes — and the residual GT error points *in LlamaParse's favor*.**
- The GT was already independently validated (`GT_VALIDATION.md`): 99.5% printed-number fidelity,
  cross-family judge, hand audit. The v1→v2 GT correction *helped* the parsers (LlamaParse charts +6.4).
- Hand-auditing agentic LlamaParse's **lowest**-scoring pages (where anti-parser GT bias would surface):
  they are dense **label-free charts** and **sparse checkmark grids** — exactly the page types the GT
  audit already flagged as the residual-error zone, and where *every* vendor struggles.
- **Adjudicated example — Alpha p14** (a chart page the judge scored LlamaParse 25% recall / 70%
  "unsupported"): agentic LlamaParse *tabulated the chart data* (Parc FY19 = 6.5). Reading the page image,
  the chart has a **broken Y-axis** starting near 6 — **LlamaParse's 6.5 is correct and the GT's ~4.7 is
  wrong** (a misread of the axis break, below the lowest gridline). The judge penalized LlamaParse for
  disagreeing with an *erroneous* GT estimate.
- **Implication:** there is **no GT bias against LlamaParse**. The residual GT chart-estimation error
  *under-credits* the most precise vendors — including agentic LlamaParse — so its true quality is
  **≥** the measured figure. This is a symmetric caveat already disclosed in `GT_VALIDATION.md §6`.

---

## 2. The headline re-measurement (fair total, full 599 pages)

Same vendor extractions for the other 7, same blind judges, same prompt/shuffle/caps; **only LlamaParse's
tier changed** (accurate → agentic). Scores below hold **page weights fixed at the canonical values** so
the only variable is information recall (see §3 — this is essential).

| Vendor | gpt-5 judge acc→agentic | Gemini judge acc→agentic |
|---|---|---|
| Gemini 3.5 Flash | 91.8 → 91.7 | 97.3 → 97.3 |
| gpt-5 (file) ◆ | 91.0 → 91.0 | 96.4 → 96.3 |
| gpt-5 (image) ◆ | 91.3 → 91.0 | 97.3 → 97.2 |
| **LlamaParse** | **71.1 → 89.6 (+18.5)** | **74.1 → 95.9 (+21.8)** |
| Gemini 3.1 Flash-Lite | 89.9 → 89.6 | 95.3 → 95.3 |
| Landing AI | 87.4 → 86.9 | 95.5 → 95.2 |
| PyMuPDF | 84.2 → 84.4 | 83.7 → 83.4 |
| Tesseract | 63.8 → 64.5 | 76.7 → 76.6 |
| **max |Δ| of the 7 unchanged vendors** | **0.69 pp** | **0.27 pp** |

**Ranking change for LlamaParse:** from **8th/last** (below Tesseract on weighted recall in the original
table) → **4th of 8**, above Landing AI and PyMuPDF, level with Gemini Flash-Lite, just behind the
gpt-5 / Gemini-Flash top tier. Both judge families agree. The 7 unchanged vendors confirm the re-judge is
reproducible — the +18.5/+21.8 is real signal, not drift.

---

## 3. Methodology note — control for the judge-assigned weight re-roll

`fair_total = Σ(info_recall × page_info_weight) ÷ Σ(page_info_weight)`. The **`page_info_weight` is
assigned by the judge** and is re-rolled on every fresh judging pass. A naive accurate-vs-agentic
comparison conflates (a) LlamaParse's recall gain with (b) weight re-roll, which shifts *every* vendor's
weighted average by ±1–4 pp even when their per-page recall is unchanged. **We therefore hold the weights
fixed at the canonical accurate-run values for both sides**, so the comparison isolates recall. (The raw,
weight-re-rolled numbers told the same LlamaParse story but added spurious ±1–4 pp wobble on the other
vendors; fixing weights removes it.) Re-judges that change one input should freeze judge-assigned
weights — a reusable rule for this benchmark.

---

## 3b. The one place agentic does NOT help — structural page classification

For completeness we also re-ran the **page-category classification** eval (the project's original task:
label each page Text / Table / Chart-Diagram / Mixed / Cover-Divider / Image, scored vs the answer key via
the area-based reducer `llamaparse_reduce.py`). Here the agentic tier **regresses**:

| Tier | Overall accuracy | Macro-F1 | Cover/Divider recall | Table recall |
|---|---:|---:|---:|---:|
| `accurate` (canonical for this task) | **47.9%** | 35.8% | 82% | 95% |
| `agentic` | **42.2%** | 29.1% | **35%** | 59% |

**Why agentic is *worse* at page-typing — and it's the mirror image of the content-extraction result.** The
reducer types a page from region *area* (sparse page → Cover; table-area-dominant → Table). The agentic
tier extracts far more text on **every** page, so it inflates the text-area signal: **28 of 55 Cover/Divider
pages flipped to "Text"** because their text-area rose above the sparseness threshold (e.g. Alpha p1
text-area 0.098→0.290, p30 0.040→0.168 — all crossing the `COVER_TEXT=0.12` cutoff). Same for table-dominant
pages diluted by extra prose. Chart/Diagram stays **0%** in both tiers — neither emits a chart/diagram region
type (`charts` array empty), so those pages always fall to whichever of text/table dominates.

**Reading:** "most capable tier" is **task-dependent.** For *content extraction* (the headline evals) agentic
is decisively better (+18–22 pp). For *structural page classification* the accurate tier's sparser output
suits an area heuristic better; agentic's content-richness is actively counterproductive there. We hold the
reducer thresholds fixed (calibrated from feature semantics, never fitted to the key), so this is the honest
same-reducer comparison; re-tuning thresholds to agentic's area distribution would be fitting-to-the-key and
is not done. The accurate-tier scorecard (`results/LlamaParse_v3.md`) remains canonical for the
classification task; the agentic scorecard is `results/LlamaParse_agentic_v3.md`.

## 4. Reproduce

```
# 1. re-parse at agentic tier (needs LLAMA_CLOUD_API_KEY credits)
python3 scripts/llamaparse_fetch_agentic.py
# 2. collect from agentic raw, using LlamaParse's canonical page md
LP_RAW_DIR=ground_truth/llamaparse_agentic/raw LP_USE_PAGE_MD=1 \
  python3 scripts/collect_extractions.py llamaparse
python3 scripts/build_vendor_md.py
# 3. re-judge (466 Alpha+IAR cached; weights frozen for comparison)
FT_GT_CAP=16000 FT_VEND_CAP=16000 GT_MD=results/_gt_markdown.json \
  FT_CACHE=ground_truth/fair_total_judge_agentic \
  FT_OUT=results/_fair_total_judging_agentic.json python3 scripts/score_fair_total.py 8
# (Gemini judge: scripts/score_fair_total_gemini.py with the _gemini_agentic paths)
# 4. category-classification eval on agentic (§3b) — same fixed reducer, agentic raw
LP_RAW_DIR=ground_truth/llamaparse_agentic/raw LP_OUT_SUFFIX=_agentic \
  python3 scripts/llamaparse_reduce.py
python3 scripts/score_solution.py results/_llamaparse_agentic_solution.json --name LlamaParse_agentic_v3
```

Backups: accurate-tier raw at `ground_truth/llamaparse/raw/`, accurate extract at
`results/_extract_llamaparse_accurate.json`, accurate vendor md at
`results/vendor_md/_mode_backups/llamaparse_accurate.md`.
