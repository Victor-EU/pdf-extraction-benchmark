# Fair Total — STRUCTURE-AWARE document-level information capture

> **Scores are structure-aware as of 2026-06-14.** A value counts as captured only if its **binding is recoverable** — which row/column/series/node/entity it belongs to — because on finance / M&A / consulting documents a number bound to the wrong row is an *active downstream error*, worse than an omission. Correct structure described in prose still earns full credit (not a formatting test); on unstructured pages (prose, dividers) the metric reduces to ordinary content recall. The prior **content-recall** rubric (information present, ignoring binding) is preserved as a diagnostic column and in `*_content.json`. See [`../STRUCTURE_AWARE_SCORING.md`](../STRUCTURE_AWARE_SCORING.md).

Each vendor's full 599-page extraction was diffed, page by page, against a ground-truth markdown transcription (`ground_truth/GROUND_TRUTH.md`) by a blind gpt-5 judge that **credits equivalent phrasing** but requires the correct bindings to be recoverable.

**Fair total** = Σ(info_recall × page_info_weight) ÷ Σ(page_info_weight) over all pages — a true ratio of *correctly-bound information captured to total information present*, weighted by how much real content each page holds. It is NOT an average of arbitrary dimension scores.

> ◆ gpt-5 built the ground truth (same model family), so its two rows are an **upper bound by construction** — reported for context, not directly comparable. Every other vendor is graded cleanly.

## The fair total

| Vendor | **Fair total** (structure-aware) | Content recall (diagnostic) | Structure gap | Unsupported (fidelity) |
|---|---:|---:|---:|---:|
| Gemini 3.5 Flash | **89%** | 92% | −3 | 8% |
| Landing AI | **86%** | 89% | −3 | 11% |
| Gemini 3.1 Flash-Lite | **86%** | 90% | −4 | 8% |
| LlamaParse | **86%** | 90% | −4 | 10% |
| PyMuPDF | **68%** | 84% | −16 | 5% |
| LiteParse | **62%** | 80% | −18 | 8% |
| Tesseract | **52%** | 64% | −12 | 15% |
| gpt-5 (image) ◆ | **88%** | 91% | −3 | 9% |
| gpt-5 (file) ◆ | **87%** | 91% | −4 | 9% |

> **Structure gap** = content recall − structure-aware fair total = the share of a vendor's apparent capture that does NOT survive a binding check. The largest gaps (LiteParse −18, PyMuPDF, Tesseract) mark tools that recover characters but lose structure; a small gap marks downstream-usable output. LiteParse's gap is the widest of all: its heuristic markdown emits table/heading *shapes* (table-presence 81%, well above PyMuPDF's 57%) but on dense multi-column finance pages its grid projection merges adjacent columns into a jumble whose bindings the judge cannot recover — so the table-shaped output is not rewarded, and it scores *below* PyMuPDF's honest flat dump (62 vs 68). **Unsupported** now counts actively wrong bindings (a value under the wrong key) as contradictions.

## Fair total by page category (structure-aware)

| Vendor | Text | Table | Chart | Mixed | Cover | Image |
|---|---:|---:|---:|---:|---:|---:|
| Gemini 3.5 Flash | 95% | 87% | 84% | 93% | 84% | 82% |
| Landing AI | 95% | 86% | 78% | 90% | 82% | 88% |
| Gemini 3.1 Flash-Lite | 94% | 85% | 78% | 89% | 85% | 68% |
| LlamaParse | 96% | 85% | 76% | 92% | 77% | 42% |
| PyMuPDF | 80% | 71% | 54% | 79% | 51% | 28% |
| LiteParse | 85% | 60% | 44% | 71% | 50% | 54% |
| Tesseract | 78% | 50% | 33% | 59% | 31% | 37% |
| gpt-5 (image) ◆ | 96% | 85% | 82% | 92% | 92% | 90% |
| gpt-5 (file) ◆ | 94% | 83% | 82% | 92% | 89% | 79% |

