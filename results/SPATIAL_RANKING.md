# Spatial-relationship ranking — insurance forms (vendor vs ground truth)

> **Why this metric.** These are FORMS: a value's meaning lives entirely in its 2-D position — which label it sits beside, which option a tick belongs to, which row×column a cell occupies. A parser that recovers every character but detaches it from its position has captured nothing usable. This ranking scores ONLY the spatial relationships (prose recall is ignored), split into the three that matter on these forms, judged blind by **both** a gpt-5 and a Gemini 3.5 Flash judge against `ground_truth/GROUND_TRUTH.md` (`scripts/score_spatial.py`).

- **field** = field-label → value binding (value attached to the *correct* label)
- **check** = checkbox/radio state bound to the correct option (the most consequential, purely-spatial call)
- **cell** = table cell placed in the correct row×column
- **SPATIAL** = per-page composite (field & check weighted 1.0, cell 0.8), weighted by each page's spatial density

> ◆ = ground-truth co-author (Gemini, and lightly the legacy Landing AI), so its scores are an **upper bound** and are **not ranked**. Cleanly graded: **gpt-5 (image), LlamaParse, PyMuPDF, Tesseract, LiteParse**. Landing AI is shown on its current **DPT-2** model. **n = 7 pages** — read the wide gaps as signal, the few-point gaps as noise.

## gpt-5 judge

| Rank | Vendor | **SPATIAL** | field | check | cell |
|---:|---|---:|---:|---:|---:|
| 1 | Mistral OCR 4 | **97%** | 96% | 100% | 95% |
| 2 | gpt-5 (image) | **84%** | 89% | 85% | 75% |
| 3 | LiteParse | **39%** | 67% | 22% | 15% |
| 4 | PyMuPDF | **32%** | 66% | 0% | 17% |
| 5 | LlamaParse | **31%** | 62% | 0% | 35% |
| 6 | Tesseract | **30%** | 58% | 6% | 10% |
| ◆ | Gemini 3.5 Flash ◆ | 99% | 98% | 100% | 98% |
| ◆ | Landing AI (DPT-2) ◆ | 92% | 93% | 94% | 88% |

## Gemini judge

| Rank | Vendor | **SPATIAL** | field | check | cell |
|---:|---|---:|---:|---:|---:|
| 1 | Mistral OCR 4 | **97%** | 98% | 97% | 95% |
| 2 | gpt-5 (image) | **85%** | 92% | 84% | 72% |
| 3 | Tesseract | **49%** | 76% | 31% | 28% |
| 4 | LiteParse | **45%** | 68% | 27% | 33% |
| 5 | LlamaParse | **38%** | 57% | 0% | 53% |
| 6 | PyMuPDF | **36%** | 74% | 0% | 23% |
| ◆ | Gemini 3.5 Flash ◆ | 100% | 100% | 100% | 100% |
| ◆ | Landing AI (DPT-2) ◆ | 86% | 94% | 87% | 69% |

