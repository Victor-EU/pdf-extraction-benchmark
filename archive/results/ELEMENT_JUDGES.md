# Element-type leaderboard — gpt-5 judge vs cross-family Gemini judge

Same vendor extractions, same fixed GT element inventory (Stage A), same blind shuffle. Only the judge model family differs. Agreement on the per-type winner rules out judge-family bias.

| Element type | gpt-5 winner | Gemini winner | agree? |
|---|---|---|:--:|
| Data tables | LlamaParse | Gemini 3.5 Flash | ✗ |
| Charts | Gemini 3.5 Flash | Gemini 3.5 Flash | ✓ |
| Diagrams | Gemini 3.5 Flash | Landing AI | ✗ |
| KPI callouts | Gemini 3.5 Flash | Landing AI | ✗ |
| Narrative | Gemini 3.5 Flash | Gemini 3.5 Flash | ✓ |
| Titles | Gemini 3.5 Flash | LlamaParse | ✗ |
| Chrome | Gemini 3.5 Flash | Gemini 3.5 Flash | ✓ |

## Data tables — recall by judge

| Vendor | gpt-5 judge | Gemini judge | Δ |
|---|---:|---:|---:|
| LlamaParse | 97 | 98 | +1 |
| Gemini 3.5 Flash | 97 | 98 | +1 |
| Gemini 3.1 Flash-Lite | 96 | 98 | +1 |
| gpt-5 (file) | 95 | 96 | +1 |
| gpt-5 (image) | 95 | 97 | +2 |
| Landing AI | 93 | 97 | +3 |
| PyMuPDF | 93 | 93 | -0 |
| Tesseract | 69 | 84 | +15 |

## Charts — recall by judge

| Vendor | gpt-5 judge | Gemini judge | Δ |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 90 | 97 | +7 |
| gpt-5 (file) | 89 | 97 | +8 |
| gpt-5 (image) | 88 | 96 | +8 |
| Gemini 3.1 Flash-Lite | 86 | 93 | +7 |
| Landing AI | 85 | 96 | +11 |
| LlamaParse | 83 | 93 | +10 |
| PyMuPDF | 83 | 74 | -9 |
| Tesseract | 41 | 44 | +2 |

## Diagrams — recall by judge

| Vendor | gpt-5 judge | Gemini judge | Δ |
|---|---:|---:|---:|
| gpt-5 (image) | 92 | 93 | +1 |
| Gemini 3.5 Flash | 92 | 94 | +2 |
| gpt-5 (file) | 89 | 91 | +2 |
| Landing AI | 89 | 95 | +6 |
| Gemini 3.1 Flash-Lite | 87 | 90 | +2 |
| LlamaParse | 83 | 86 | +3 |
| PyMuPDF | 50 | 49 | -1 |
| Tesseract | 45 | 46 | +1 |

## KPI callouts — recall by judge

| Vendor | gpt-5 judge | Gemini judge | Δ |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 100 | 100 | -0 |
| PyMuPDF | 100 | 99 | -1 |
| gpt-5 (image) | 100 | 100 | +0 |
| gpt-5 (file) | 100 | 100 | -0 |
| Gemini 3.1 Flash-Lite | 98 | 99 | +1 |
| Landing AI | 98 | 100 | +2 |
| LlamaParse | 95 | 95 | +0 |
| Tesseract | 81 | 83 | +2 |

## Narrative — recall by judge

| Vendor | gpt-5 judge | Gemini judge | Δ |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 100 | 100 | +0 |
| LlamaParse | 100 | 100 | -0 |
| gpt-5 (image) | 99 | 100 | +0 |
| Gemini 3.1 Flash-Lite | 99 | 99 | +0 |
| Landing AI | 99 | 99 | +0 |
| gpt-5 (file) | 98 | 99 | +0 |
| PyMuPDF | 97 | 97 | +0 |
| Tesseract | 96 | 97 | +0 |

## Titles — recall by judge

| Vendor | gpt-5 judge | Gemini judge | Δ |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 100 | 99 | -1 |
| gpt-5 (file) | 100 | 99 | -0 |
| LlamaParse | 100 | 100 | +0 |
| gpt-5 (image) | 100 | 99 | -0 |
| Gemini 3.1 Flash-Lite | 99 | 99 | -0 |
| PyMuPDF | 97 | 97 | +0 |
| Landing AI | 96 | 96 | +0 |
| Tesseract | 92 | 93 | +2 |

## Chrome — recall by judge

| Vendor | gpt-5 judge | Gemini judge | Δ |
|---|---:|---:|---:|
| gpt-5 (file) | 92 | 96 | +4 |
| gpt-5 (image) | 91 | 96 | +4 |
| Gemini 3.5 Flash | 91 | 95 | +4 |
| Gemini 3.1 Flash-Lite | 88 | 92 | +3 |
| LlamaParse | 87 | 94 | +6 |
| Landing AI | 87 | 94 | +7 |
| PyMuPDF | 65 | 70 | +5 |
| Tesseract | 52 | 66 | +14 |

