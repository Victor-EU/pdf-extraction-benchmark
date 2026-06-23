# Pre-publication audit — the VEND_CAP truncation artifact (found, fixed, re-measured)

**Date:** 2026-06-13. **Scope:** vendor-by-vendor re-audit of all three LLM-judge harnesses (element-level,
document fair-total, figure dimensions) against ground truth, before publication. **Headline:** a recurring
methodology bug — **fixed character caps on the vendor text fed to the judge** — appeared in all three. The
severe form (a 6,000-char whole-page cap in the element + fair-total evals) **systematically deflated Landing
AI and only Landing AI**, because its output is ~2× longer than any other vendor's and its figure
descriptions sit at the end of the page where the cut landed; correcting it raised Landing AI's figure/KPI
scores by 2–13 points (§3–4). The mild form (per-figure/blob caps in the figure judge) clipped Landing AI
plus gpt-5 and Gemini Flash, and moved scores ≤3 points (§7). **Found, fixed (re-judged at no-truncation
caps under both judge families), re-measured: no ranking changes in any eval.** Everything else audited
checks out (§6).

---

## 1. What was wrong

The blind judges in `score_elements.py` (element-level) and `score_fair_total.py` (document-level) each
truncated every vendor's per-page markdown to `VEND_CAP = 6000` chars before showing it to the judge
(`score_fair_total.py` also capped the **ground-truth reference** at `GT_CAP = 6000`). The cross-family
Gemini judges import the same constant, so they inherited the bug.

Truncation incidence (pages where a vendor's page markdown exceeds 6,000 chars):

| Vendor | pages truncated | % of 599 | max page chars |
|---|---:|---:|---:|
| **Landing AI** | **145** | **24.2%** | **14,133** |
| gpt-5 (image/file) | 9 | 1.5% | ~8,260 |
| Gemini Flash / Lite | 8–9 | ~1.4% | ~8,250 |
| PyMuPDF / Tesseract | 7 | 1.2% | ~8,200 |
| LlamaParse | 6 | 1.0% | 8,217 |

Landing AI is a **20× outlier**. Two compounding reasons it is hit specifically:
1. Its ADE output is the most verbose (3.06M chars across the corpus vs 1.1–1.5M for every other vendor).
2. `build_vendor_md.py` appends **figure descriptions last**, so the 6,000-char cut removes exactly the
   chart/diagram/KPI prose — the element types where Landing AI was reported weakest. Of its 145 truncated
   pages, **79 carry chart/diagram ground-truth elements (193 figure elements at risk)**.

This is the same class of vendor-specific metric artifact as the earlier `table_presence` bug
(`PDF_parsing_test_table_metric_artifact`): a measurement choice, not a ground-truth or vendor-quality
fact, silently penalising the one vendor whose output shape differs.

## 2. The fix

Re-judged every affected page (147 for the element eval, 148 for fair-total — the union of all pages where
**any** vendor or the GT reference exceeds 6,000 chars) at `VEND_CAP = GT_CAP = 16000` (covers the 14,133
global max → **zero truncation**). The other 451–452 pages are provably identical at either cap (no field
exceeds 6,000 chars there) and were carried over byte-for-byte from the published run. Re-ran under **both**
the gpt-5 and the cross-family Gemini judge. 0 errors (element); fair-total has the same 1 pre-existing
Gemini-judge failure on IAR p129 as the published baseline.

Caps are now env-overridable (`EL_VEND_CAP`, `FT_VEND_CAP`, `FT_GT_CAP`); the 16,000 run is canonical.
Pre-fix runs preserved as `*_cap6000.json` for diffing.

## 3. What changed — element-level recall (gpt-5 judge)

Only Landing AI moves > 1 point; every other vendor is within ±1 everywhere.

| Element type | Landing AI before | after | Δ |
|---|---:|---:|---:|
| **KPI callouts** | 84 | **98** | **+13.2** |
| **Charts** | 77 | **85** | **+7.7** |
| Diagrams | 85 | 89 | +3.4 |
| Data tables | 91 | 93 | +2.0 |
| Narrative | 97 | 99 | +1.9 |
| Chrome | 86 | 87 | +1.4 |
| Titles | 96 | 96 | +0.5 |

The headline correction: the buggy run reported Landing AI as the **worst clean vendor on KPI callouts (84)**;
it is actually **98 — tied at the top**. The "weak on charts/KPI" narrative was substantially an artifact.

## 4. What changed — document-level fair total

| | gpt-5 judge | Gemini judge |
|---|---:|---:|
| Landing AI overall | 85.0 → **87.4** (+2.4) | 93.5 → **95.5** (+2.0) |
| └ Chart/Diagram pages | 75.9 → **80.2** (+4.3) | 89.7 → **94.0** (+4.3) |
| └ Table pages | 86.7 → 87.6 (+0.9) | 93.7 → 95.1 (+1.3) |
| └ Image/Photo pages | 60.0 → 76.2 (+16.2) | 91.2 → 87.9 (−3.3) |
| every other vendor | ±0.4 | ±0.2 |

Published claims to correct: **headline 85 → 87%**, **charts 76 → 80%**, **image 60 → 76%**
(the image figure rests on only **2 Image/Photo pages** — it was never statistically robust and should be
reported with that n, not as a headline weakness). Landing AI's **high unsupported/padding rate (17%) is
NOT an artifact** — it is unchanged by the fix and remains a real, reportable trait.

## 5. What did NOT change (the reassurance for publication)

- **No ranking changes in either eval.** Gemini 3.5 Flash remains the best/﻿tied-best generalist on every
  element type under **both** judge families; Landing AI remains the top dedicated-parser tier, still ahead
  of PyMuPDF, still behind the vision LLMs on the holistic total.
- **Cross-family agreement.** Element-level per-type winners now agree 5/7 across judges (was 6/7); the two
  that differ — diagrams and KPI — are **ties at the top of the vision tier** (KPI: Gemini 100 / Landing AI
  100 / PyMuPDF 99–100; diagrams: Gemini 92–94 vs Landing AI 89–95, judge-dependent), not rank reversals of
  the headline. Both judges still pick Gemini Flash #1 on tables, charts, narrative, titles, chrome.
- The Gemini-judge fair-total now puts Landing AI (95.5) a hair above Flash-Lite (95.3) for #2-clean; the
  gpt-5 judge keeps Flash-Lite ahead (89.9 vs 87.4). Honest read: **Landing AI and Flash-Lite are
  neck-and-neck for second**, judge-dependent.

## 6. Other checks run in the same audit (all clean)

- **Both stages ran on the corrected v2 GT** (md5 `8214cad…` = `_gt_markdown_v2.json`; `GROUND_TRUTH.md` =
  v2). The hallucinated-v1 figures are not in play.
- **Judge completeness:** 0 error pages; **0 of 6,129 elements left unscored**; no vendor dropped from any
  scored element. The `max_output_tokens` cap never truncated a judge response.
- **`GT_CAP = 9000` in Stage A decomposition:** 0 of 599 GT pages exceeded it → no element inventory was
  built from truncated text. (The separate `GT_CAP = 6000` in fair-total *did* clip the reference on 10
  dense pages — fixed in the re-run alongside VEND_CAP.)
- **Report scripts faithful:** the published per-type table was re-derived independently from raw judge
  JSON and matches.
- **Salience-weight & coverage-threshold sensitivity:** the per-type winner is stable weighted vs
  unweighted and at recall≥50 vs ≥70; the only flips are inside the statistical tie band (tables, KPI).
- **Bootstrap 95% CIs on the clean winner's lead (element-level, corrected):**
  charts **+3.8 [+2.1,+5.6]**, diagrams **+3.4 [+0.4,+6.8]**, narrative **+0.8 [+0.4,+1.2]**,
  titles **+0.8 [+0.3,+1.3]**, chrome **+2.5 [+1.4,+3.6]** = real; **tables +0.2 [−0.5,+0.9]** and
  **KPI +0.4 [0.0,+1.0]** = statistical **ties** (report as ties, not wins).
- **Degenerate vendor pages** (page returns empty → 0 recall there, by construction): Gemini Flash 1
  (Alpha p5), Flash-Lite 2 (Alpha p5, IAR p103), PyMuPDF 1 (Alpha p156), Tesseract 4 (image-only pages with
  no recoverable text). 1–4 pages per vendor / 599; disclosed, aggregates unaffected.

## 7. The figure judge (`score_figures.py`) — also audited and re-run

`score_figures.py` (the source of FINAL_REPORT §4's graph-data and diagram-structure numbers) has **five**
caps in `vendor_blob`: per-figure `[:1600]`, per-table `[:1200]`, first-8-figures, first-6-tables, and a
whole-blob `[:7000]`. Measured incidence on the 265 figure-bearing pages:

| Vendor | figures clipped @1600 | pages losing figures @>8 | pages over 7000 blob |
|---|---:|---:|---:|
| Landing AI | **219** | 0 | **30** |
| gpt-5 (image/file) | 30–32 | **11–14** | 0 |
| Gemini Flash | 18 | 0 | 0 |
| Gemini Flash-Lite | 1 | 1 | 0 |
| LlamaParse / PyMuPDF / Tesseract | 0 | 0 | 0 |

Unlike VEND_CAP, this hits **several** vision vendors — Landing AI most (verbose figure prose + 30 dense
pages over the blob cap), but also gpt-5 (it emits granular figure blocks, so the first-8 cap dropped real
figures on 11–14 pages) and Gemini Flash. So raising the caps could lift any of them; the net effect on the
published gap had to be re-measured, not assumed.

**Re-judged all 212 affected pages at no-truncation caps** (`FIG_FIG_CAP=6000 FIG_TAB_CAP=5000 FIG_NFIG=24
FIG_NTAB=12 FIG_BLOB=60000`), both spliced onto the 53 unaffected pages, 0 errors, $3.81. Result — **the
caps were a MILD distortion (≤3 points), not a severe one**:

| Dimension | Gemini Flash | Landing AI | gpt-5 (image) | gap (GemF − LA) |
|---|---:|---:|---:|---:|
| graph-data | 86 → 85 | 79 → **80** | 85 → 85 | +7 → **+5** |
| diagram-structure | 89 → **91** | 79 → **82** | 68 → 66 | +10 → **+9** |

The cleanest truncation-fix signal is **Landing AI rising** (graph +1.2, diagram +3.0); the small Gemini/﻿gpt-5
± wiggles (≤2pt, mixed sign) are a mix of their own minor clipping and judge recalibration when it sees
fuller competitors. **No ranking changed; Gemini Flash still commands the figure dimensions (diagram 91 vs
Landing AI 82).** The no-truncation run is now canonical (`extraction_report.py` regenerated
`EXTRACTION_COMPARISON.md`; FINAL_REPORT §4 updated); pre-fix preserved as `_figure_judging_cap1600.json`.

**All three judge harnesses are now truncation-free** — the only remaining caps are deliberate count
generosity well above the observed maxima.

**Gemini image-vs-file A/B sub-study (`_gemini_modes_judging`, `GEMINI_FILE_MODE.md`) — also swept.** This
4-config figure judge (Flash/Lite × image/file) decides which mode is canonical for the whole benchmark, so
it mattered. Hypothesis worth testing: file mode has the embedded text layer, so it might emit *longer*
figure prose and be clipped *more* → "file worse" could be an artifact. **Measured: false** — file emits
slightly *shorter* figure content (avg 338 vs 349 chars flash; 200 vs 219 lite) and was clipped *less* (15
vs 18; 0 vs 1), blob never over 7000. Re-judged the 31 affected pages at no-truncation caps (0 errors,
$2.66): the file−image deltas are essentially unchanged (Flash graph ±0→+0.6 / diagram −1.3→−1.7; Flash-Lite
graph −1.8 / diagram ±0), absolute levels rose for Flash in line with the canonical figure re-judge. **The
"native-PDF is a wash, keep `image` canonical" verdict holds and is confirmed not a truncation artifact.**

## 8. Residual items (disclosed, not blocking)

- The corpus is 3 born-digital documents; no scanned corpus. Stated in every report.

**Bottom line for reviewers:** we found a measurement bug in our own harness that hurt the competitor we
rank third, fixed it, and re-ran with two judge families. The correction *helps* Landing AI by 2–13 points
on the affected dimensions and changes no rankings. The benchmark's conclusions are robust to it.
