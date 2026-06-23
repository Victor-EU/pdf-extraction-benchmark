# Scorecard: openai_gpt5_image

Pages scored: 599  |  predictions missing: 0

## Overall accuracy: 484/599 = 80.8%

## Accuracy by category (recall) + precision/F1

| Category | Support | Recall | Precision | F1 |
|---|---:|---:|---:|---:|
| Text | 151 | 85% | 77% | 81% |
| Table | 126 | 92% | 83% | 88% |
| Chart/Diagram | 153 | 85% | 91% | 88% |
| Mixed | 112 | 48% | 57% | 52% |
| Cover/Divider | 55 | 98% | 100% | 99% |
| Image/Photo | 2 | 50% | 100% | 67% |

Macro-avg F1 (categories present): 79.1%

## Confusion matrix (rows = TRUE, cols = predicted)

| true \ pred | Text | Table | Chart | Mixed | Cover | Image | miss |
|---|---:|---:|---:|---:|---:|---:|---:|
| Text | 129 | 3 | 2 | 17 | 0 | 0 | 0 |
| Table | 2 | 116 | 2 | 6 | 0 | 0 | 0 |
| Chart/Diagram | 2 | 4 | 130 | 17 | 0 | 0 | 0 |
| Mixed | 33 | 16 | 9 | 54 | 0 | 0 | 0 |
| Cover/Divider | 1 | 0 | 0 | 0 | 54 | 0 | 0 |
| Image/Photo | 0 | 0 | 0 | 1 | 0 | 1 | 0 |

## Speed
- pages with timing: 599
- mean: 4.12s/page  | min 1.81s | max 17.28s
- total wall (sum): 2465s for 599 pages

## Cost
- total: $1.81  | mean $0.0030/page  | for 599 pages
