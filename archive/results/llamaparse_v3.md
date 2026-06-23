# Scorecard: LlamaParse_v3

> **Tier note (2026-06-13).** This is the **`accurate`-tier** scorecard for the *page-category
> classification* task, and it remains canonical for this task. Re-running at the **`agentic` tier**
> *regresses* to **42.2%** (`LlamaParse_agentic_v3.md`): agentic extracts more text on every page, which
> inflates the area-based reducer's text signal and flips 28/55 Cover/Divider pages to "Text". Agentic is
> decisively better for *content extraction* (+18–22 pp, see `AUDIT_LLAMAPARSE_MODE.md` §2) but worse for
> *structural page-typing* — "most capable tier" is task-dependent. (Scored against the current
> `final_answer_key.json`, accurate = 47.9%; the 48.1% below is vs the key snapshot at original run time.)

Pages scored: 599  |  predictions missing: 0

## Overall accuracy: 288/599 = 48.1%

## Accuracy by category (recall) + precision/F1

| Category | Support | Recall | Precision | F1 |
|---|---:|---:|---:|---:|
| Text | 149 | 72% | 66% | 69% |
| Table | 128 | 95% | 35% | 52% |
| Chart/Diagram | 152 | 0% | 0% | 0% |
| Mixed | 113 | 12% | 52% | 20% |
| Cover/Divider | 55 | 82% | 69% | 75% |
| Image/Photo | 2 | 0% | 0% | 0% |

Macro-avg F1 (categories present): 35.9%

## Confusion matrix (rows = TRUE, cols = predicted)

| true \ pred | Text | Table | Chart | Mixed | Cover | Image | miss |
|---|---:|---:|---:|---:|---:|---:|---:|
| Text | 107 | 23 | 0 | 7 | 12 | 0 | 0 |
| Table | 5 | 122 | 0 | 1 | 0 | 0 | 0 |
| Chart/Diagram | 14 | 131 | 0 | 5 | 2 | 0 | 0 |
| Mixed | 29 | 64 | 0 | 14 | 6 | 0 | 0 |
| Cover/Divider | 8 | 2 | 0 | 0 | 45 | 0 | 0 |
| Image/Photo | 0 | 2 | 0 | 0 | 0 | 0 | 0 |

## Speed
- pages with timing: 599
- mean: 0.63s/page  | min 0.40s | max 1.05s
- total wall (sum): 377s for 599 pages

## Cost
- total: $0.00  | mean $0.0000/page  | for 599 pages
