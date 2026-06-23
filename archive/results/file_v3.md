# Scorecard: file_v3

Pages scored: 599  |  predictions missing: 0

## Overall accuracy: 483/599 = 80.6%

## Accuracy by category (recall) + precision/F1

| Category | Support | Recall | Precision | F1 |
|---|---:|---:|---:|---:|
| Text | 149 | 92% | 69% | 79% |
| Table | 128 | 92% | 85% | 88% |
| Chart/Diagram | 152 | 89% | 93% | 91% |
| Mixed | 113 | 34% | 68% | 45% |
| Cover/Divider | 55 | 98% | 95% | 96% |
| Image/Photo | 2 | 50% | 33% | 40% |

Macro-avg F1 (categories present): 73.2%

## Confusion matrix (rows = TRUE, cols = predicted)

| true \ pred | Text | Table | Chart | Mixed | Cover | Image | miss |
|---|---:|---:|---:|---:|---:|---:|---:|
| Text | 137 | 4 | 1 | 4 | 3 | 0 | 0 |
| Table | 6 | 118 | 1 | 3 | 0 | 0 | 0 |
| Chart/Diagram | 6 | 1 | 135 | 10 | 0 | 0 | 0 |
| Mixed | 49 | 16 | 8 | 38 | 0 | 2 | 0 |
| Cover/Divider | 1 | 0 | 0 | 0 | 54 | 0 | 0 |
| Image/Photo | 0 | 0 | 0 | 1 | 0 | 1 | 0 |

## Speed
- pages with timing: 599
- mean: 6.98s/page  | min 4.06s | max 97.02s
- total wall (sum): 4181s for 599 pages

## Cost
- total: $2.00  | mean $0.0033/page  | for 599 pages
