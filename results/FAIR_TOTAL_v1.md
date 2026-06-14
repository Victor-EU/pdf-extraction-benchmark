# Fair Total — document-level information capture (paraphrase-tolerant)

Each vendor's full 599-page extraction was diffed, page by page, against a ground-truth markdown transcription (`ground_truth/GROUND_TRUTH.md`) by a blind gpt-5 judge that **credits equivalent phrasing**: a table, chart, or diagram described in different-but-correct words — with the same numbers and relationships — counts as fully captured. This answers "how much of the document's actual information did this vendor convey," not "how many tokens overlap."

**Fair total** = Σ(info_recall × page_info_weight) ÷ Σ(page_info_weight) over all pages — a true ratio of *total information captured to total information present*, weighted by how much real content each page holds (a dense data table counts far more than a divider). It is NOT an average of arbitrary dimension scores.

> ◆ gpt-5 built the ground truth (same model family), so its two rows are an **upper bound by construction** — reported for context, not directly comparable. Every other vendor is graded cleanly.

## The fair total

| Vendor | **Fair total** (info captured) | Mean recall (unweighted) | Unsupported claims (fidelity) |
|---|---:|---:|---:|
| Landing AI | **85%** | 85% | 17% |
| Gemini 3.5 Flash | **90%** | 91% | 8% |
| gpt-5 (image) ◆ | **91%** | 92% | 6% |
| gpt-5 (file) ◆ | **89%** | 90% | 7% |
| Gemini 3.1 Flash-Lite | **88%** | 89% | 6% |
| LlamaParse | **68%** | 69% | 9% |
| PyMuPDF | **81%** | 80% | 3% |
| Tesseract | **62%** | 62% | 13% |

> Unsupported = the share of a vendor's own claims the judge could not back from the page truth (wrong numbers, invented content) — lower is better. Read it alongside the fair total: a high total with low unsupported is genuine; a high total with high unsupported is padding.

## Fair total by page category

| Vendor | Text | Table | Chart | Mixed | Cover | Image |
|---|---:|---:|---:|---:|---:|---:|
| Landing AI | 95% | 86% | 75% | 86% | 82% | 60% |
| Gemini 3.5 Flash | 96% | 90% | 83% | 94% | 84% | 95% |
| gpt-5 (image) ◆ | 97% | 89% | 86% | 95% | 91% | 90% |
| gpt-5 (file) ◆ | 95% | 88% | 83% | 94% | 90% | 94% |
| Gemini 3.1 Flash-Lite | 95% | 90% | 79% | 93% | 83% | 89% |
| LlamaParse | 79% | 70% | 56% | 72% | 51% | 74% |
| PyMuPDF | 91% | 85% | 72% | 84% | 50% | 61% |
| Tesseract | 86% | 61% | 45% | 66% | 33% | 70% |

