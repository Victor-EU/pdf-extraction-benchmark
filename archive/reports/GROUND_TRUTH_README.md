# PDF Parsing Test — Ground Truth (Step 1)

Per-page **category answer key** for 3 PDFs (599 pages), used to score PDF-parsing
solutions on **speed, cost, and accuracy** (overall + per category).

## The answer key
- `ground_truth/reconcile/final_answer_key.json` — authoritative. One of 6 labels per page,
  plus how it was resolved, confidence, and both source opinions.
- `ground_truth/ANSWER_KEY.csv` — same, flat CSV.

### 6 categories (mutually exclusive, exhaustive — every page gets exactly one)
Text · Table · Chart/Diagram · Mixed · Cover/Divider · Image/Photo
Definitions + boundary conventions: `ground_truth/RUBRIC.md` (the locked rubric).

### Final distribution (599 pages)
Chart/Diagram 153 (26%) · Text 151 (25%) · Table 126 (21%) · Mixed 112 (19%) ·
Cover/Divider 55 (9%) · Image/Photo 2 (0%)
(Image/Photo is tiny by design: photo-filled covers/dividers are Cover/Divider **by function**.)

## How the ground truth was built (2 intelligent sources + deep-think)
1. **Claude vision** labels every page (calibrated subagents, rubric-driven). → `ground_truth/vision_full/`
2. **Landing AI ADE** parses every page; typed chunks reduced to a dominant label. → `ground_truth/landingai_full/`
3. **Reconcile**: agree (365/599 = 61%) → locked. Disagree (234) → **deep-think adjudication**
   per page (fresh re-examination of the image with both opinions), then **manual review** of
   every still-uncertain / both-overridden case (7 pages). → `ground_truth/reconcile/`
   - Tie-break outcome: vision won 198, Landing AI 30, adjudicator overrode both 6; +3 changed on my review.
- A deterministic PyMuPDF heuristic was prototyped but **dropped** as a labeling source (too weak: 32%).
  Its features remain only as throwaway diagnostics (`ground_truth/deterministic/`).

## Scoring a new parsing solution
1. Produce predictions as JSON: `[{"doc":..., "page":..., "label":<one of 6>, "seconds":<optional>, "cost_usd":<optional>}, ...]`
   (`doc` = PDF filename without `.pdf`; `page` = 1-based.)
2. Run: `python3 scripts/score_solution.py <preds.json> --name <solution_name>`
3. Get overall accuracy, per-category recall/precision/F1, confusion matrix, and speed/cost
   if timing/cost fields are present. Report saved to `results/<solution_name>.md`.

## Baselines (results/)
- `COMPARISON.md` — head-to-head table (start here).
- `pymupdf.md` — **PyMuPDF heuristic classifier: 45.4%** overall, **0.11s/page**, $0. Fair/non-circular.
- `landing_ai_baseline.md` — Landing AI ADE: **65.8%** overall, **16.6s/page** mean.
  ⚠️ CIRCULAR: Landing AI co-authored the key, so this is an inflated upper bound, NOT a fair
  benchmark. Same applies to Claude vision. Use the key to score **other** solutions fairly.
  Cost: plug Landing AI's per-page rate into the `cost_usd` field to get $/run.

## File map
```
Data/                                   3 source PDFs
ground_truth/
  RUBRIC.md                             locked 6-category rubric
  ANSWER_KEY.csv                        flat answer key
  render_full/                          599 page PNGs (1600px cap) + batches/
  vision_full/                          Claude vision labels (per batch + _consolidated)
  landingai_full/                       Landing AI raw + reduced labels
  reconcile/
    full_reconciled.json                vision-vs-LA join
    disagreements.json                  the 234 disagreements
    tiebreak_results/                   adjudicator decisions
    needs_my_review.json                7 manually-reviewed pages
    final_answer_key.json               <-- AUTHORITATIVE
scripts/                                render / vision-split / landingai / reconcile / score
results/                                solution scorecards
```
