# Scorecard: LlamaParse_v2

Pages scored: 599  |  predictions missing: 0

## Overall accuracy: 287/599 = 47.9%

## Accuracy by category (recall) + precision/F1

| Category | Support | Recall | Precision | F1 |
|---|---:|---:|---:|---:|
| Text | 150 | 71% | 66% | 68% |
| Table | 127 | 95% | 35% | 51% |
| Chart/Diagram | 152 | 0% | 0% | 0% |
| Mixed | 113 | 12% | 52% | 20% |
| Cover/Divider | 55 | 82% | 69% | 75% |
| Image/Photo | 2 | 0% | 0% | 0% |

Macro-avg F1 (categories present): 35.8%

## Confusion matrix (rows = TRUE, cols = predicted)

| true \ pred | Text | Table | Chart | Mixed | Cover | Image | miss |
|---|---:|---:|---:|---:|---:|---:|---:|
| Text | 107 | 24 | 0 | 7 | 12 | 0 | 0 |
| Table | 5 | 121 | 0 | 1 | 0 | 0 | 0 |
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
