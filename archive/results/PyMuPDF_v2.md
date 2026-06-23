# Scorecard: PyMuPDF_v2

Pages scored: 599  |  predictions missing: 0

## Overall accuracy: 271/599 = 45.2%

## Accuracy by category (recall) + precision/F1

| Category | Support | Recall | Precision | F1 |
|---|---:|---:|---:|---:|
| Text | 150 | 63% | 43% | 51% |
| Table | 127 | 33% | 79% | 47% |
| Chart/Diagram | 152 | 53% | 75% | 62% |
| Mixed | 113 | 20% | 20% | 20% |
| Cover/Divider | 55 | 58% | 84% | 69% |
| Image/Photo | 2 | 0% | 0% | 0% |

Macro-avg F1 (categories present): 41.5%

## Confusion matrix (rows = TRUE, cols = predicted)

| true \ pred | Text | Table | Chart | Mixed | Cover | Image | miss |
|---|---:|---:|---:|---:|---:|---:|---:|
| Text | 94 | 1 | 6 | 29 | 6 | 14 | 0 |
| Table | 50 | 42 | 11 | 22 | 0 | 2 | 0 |
| Chart/Diagram | 25 | 7 | 80 | 35 | 0 | 5 | 0 |
| Mixed | 48 | 3 | 7 | 23 | 0 | 32 | 0 |
| Cover/Divider | 0 | 0 | 2 | 3 | 32 | 18 | 0 |
| Image/Photo | 0 | 0 | 0 | 2 | 0 | 0 | 0 |

## Speed
- pages with timing: 599
- mean: 0.11s/page  | min 0.00s | max 1.07s
- total wall (sum): 69s for 599 pages

## Cost
- total: $0.00  | mean $0.0000/page  | for 599 pages
