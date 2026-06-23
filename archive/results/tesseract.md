# Scorecard: tesseract

Pages scored: 599  |  predictions missing: 0

## Overall accuracy: 270/599 = 45.1%

## Accuracy by category (recall) + precision/F1

| Category | Support | Recall | Precision | F1 |
|---|---:|---:|---:|---:|
| Text | 151 | 42% | 80% | 55% |
| Table | 126 | 29% | 33% | 31% |
| Chart/Diagram | 153 | 73% | 44% | 55% |
| Mixed | 112 | 21% | 19% | 20% |
| Cover/Divider | 55 | 65% | 95% | 77% |
| Image/Photo | 2 | 0% | 0% | 0% |

Macro-avg F1 (categories present): 39.6%

## Confusion matrix (rows = TRUE, cols = predicted)

| true \ pred | Text | Table | Chart | Mixed | Cover | Image | miss |
|---|---:|---:|---:|---:|---:|---:|---:|
| Text | 63 | 19 | 26 | 43 | 0 | 0 | 0 |
| Table | 10 | 36 | 49 | 31 | 0 | 0 | 0 |
| Chart/Diagram | 0 | 18 | 112 | 21 | 2 | 0 | 0 |
| Mixed | 6 | 32 | 51 | 23 | 0 | 0 | 0 |
| Cover/Divider | 0 | 2 | 17 | 0 | 36 | 0 | 0 |
| Image/Photo | 0 | 1 | 1 | 0 | 0 | 0 | 0 |

## Speed
- pages with timing: 599
- mean: 1.18s/page  | min 0.19s | max 3.41s
- total wall (sum): 706s for 599 pages

## Cost
- total: $0.00  | mean $0.0000/page  | for 599 pages
