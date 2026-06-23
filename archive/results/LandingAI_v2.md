# Scorecard: LandingAI_v2

Pages scored: 599  |  predictions missing: 0

## Overall accuracy: 397/599 = 66.3%

## Accuracy by category (recall) + precision/F1

| Category | Support | Recall | Precision | F1 |
|---|---:|---:|---:|---:|
| Text | 150 | 74% | 82% | 78% |
| Table | 127 | 72% | 98% | 83% |
| Chart/Diagram | 152 | 82% | 78% | 80% |
| Mixed | 113 | 47% | 50% | 49% |
| Cover/Divider | 55 | 27% | 71% | 39% |
| Image/Photo | 2 | 50% | 1% | 2% |

Macro-avg F1 (categories present): 55.2%

## Confusion matrix (rows = TRUE, cols = predicted)

| true \ pred | Text | Table | Chart | Mixed | Cover | Image | miss |
|---|---:|---:|---:|---:|---:|---:|---:|
| Text | 111 | 2 | 3 | 25 | 6 | 3 | 0 |
| Table | 7 | 92 | 10 | 9 | 0 | 9 | 0 |
| Chart/Diagram | 4 | 0 | 125 | 17 | 0 | 6 | 0 |
| Mixed | 12 | 0 | 16 | 53 | 0 | 32 | 0 |
| Cover/Divider | 1 | 0 | 6 | 1 | 15 | 32 | 0 |
| Image/Photo | 0 | 0 | 1 | 0 | 0 | 1 | 0 |

## Speed
- pages with timing: 599
- mean: 16.63s/page  | min 1.32s | max 159.46s
- total wall (sum): 9962s for 599 pages
