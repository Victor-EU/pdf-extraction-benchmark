# Scorecard: LlamaParse_agentic_v3

Pages scored: 599  |  predictions missing: 0

## Overall accuracy: 253/599 = 42.2%

## Accuracy by category (recall) + precision/F1

| Category | Support | Recall | Precision | F1 |
|---|---:|---:|---:|---:|
| Text | 151 | 93% | 43% | 59% |
| Table | 126 | 59% | 57% | 58% |
| Chart/Diagram | 153 | 0% | 0% | 0% |
| Mixed | 112 | 17% | 19% | 18% |
| Cover/Divider | 55 | 35% | 48% | 40% |
| Image/Photo | 2 | 0% | 0% | 0% |

Macro-avg F1 (categories present): 29.1%

## Confusion matrix (rows = TRUE, cols = predicted)

| true \ pred | Text | Table | Chart | Mixed | Cover | Image | miss |
|---|---:|---:|---:|---:|---:|---:|---:|
| Text | 141 | 5 | 0 | 4 | 1 | 0 | 0 |
| Table | 11 | 74 | 0 | 28 | 13 | 0 | 0 |
| Chart/Diagram | 55 | 46 | 0 | 47 | 5 | 0 | 0 |
| Mixed | 87 | 5 | 0 | 19 | 1 | 0 | 0 |
| Cover/Divider | 36 | 0 | 0 | 0 | 19 | 0 | 0 |
| Image/Photo | 1 | 0 | 0 | 0 | 1 | 0 | 0 |

## Speed
- pages with timing: 599
- mean: 1.32s/page  | min 1.04s | max 1.42s
- total wall (sum): 789s for 599 pages

## Cost
- total: $0.00  | mean $0.0000/page  | for 599 pages
