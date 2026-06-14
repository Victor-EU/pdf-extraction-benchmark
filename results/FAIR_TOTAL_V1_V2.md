# Fair total — v1 GT vs corrected v2 GT

Same vendor extractions, same blind gpt-5 judge, **only the ground-truth reference changed** (v2 = figure pages rebuilt with the authoritative text layer + 2400px render). This isolates the effect of correcting the GT's chart-data errors on the headline ranking.

> **Note:** both columns use the original 6,000-char judge-input cap, so they isolate the GT correction alone. A later, separate fix removed a judge-input truncation that clipped only Landing AI, raising the **canonical** numbers further (Landing AI 85.0→**87.4%**); see `AUDIT_VEND_CAP.md` and `FAIR_TOTAL.md` for current values. Ranking unchanged by either correction.

| Vendor | v1 fair total | v2 fair total | Δ (pp) | v1 unsup | v2 unsup |
|---|---:|---:|---:|---:|---:|
| Gemini 3.5 Flash | 90.0% | 91.6% | +1.6 | 8.1% | 7.6% |
| Gemini 3.1 Flash-Lite | 88.3% | 89.7% | +1.4 | 6.1% | 6.3% |
| Landing AI | 84.5% | 85.0% | +0.4 | 17.3% | 16.9% |
| PyMuPDF | 81.2% | 84.3% | +3.2 | 3.2% | 2.4% |
| LlamaParse | 68.1% | 70.9% | +2.8 | 9.0% | 8.4% |
| Tesseract | 62.2% | 64.2% | +2.0 | 13.2% | 13.1% |
| gpt-5 (image) ◆ | 91.1% | 90.9% | -0.2 | 6.2% | 7.5% |
| gpt-5 (file) ◆ | 89.0% | 90.6% | +1.6 | 7.3% | 6.9% |

**Ranking (clean vendors) v1:** Gemini 3.5 Flash > Gemini 3.1 Flash-Lite > Landing AI > PyMuPDF > LlamaParse > Tesseract

**Ranking (clean vendors) v2:** Gemini 3.5 Flash > Gemini 3.1 Flash-Lite > Landing AI > PyMuPDF > LlamaParse > Tesseract

**Ranking changed:** NO — identical order

## Chart/Diagram + Mixed fair total (where the GT was corrected)

| Vendor | Chart v1 | Chart v2 | Δ | Mixed v1 | Mixed v2 | Δ |
|---|---:|---:|---:|---:|---:|---:|
| Gemini 3.5 Flash | 82.7% | 86.8% | +4.1 | 94.1% | 94.6% | +0.5 |
| Gemini 3.1 Flash-Lite | 79.2% | 83.3% | +4.1 | 92.6% | 92.3% | -0.3 |
| Landing AI | 74.9% | 75.9% | +1.0 | 85.8% | 85.4% | -0.4 |
| PyMuPDF | 72.0% | 79.5% | +7.6 | 84.3% | 88.7% | +4.4 |
| LlamaParse | 56.4% | 62.8% | +6.4 | 72.4% | 76.2% | +3.8 |
| Tesseract | 44.7% | 49.8% | +5.0 | 66.5% | 68.8% | +2.3 |
| gpt-5 (image) ◆ | 86.2% | 86.0% | -0.2 | 95.0% | 93.9% | -1.0 |
| gpt-5 (file) ◆ | 82.5% | 87.0% | +4.4 | 93.5% | 93.8% | +0.3 |

