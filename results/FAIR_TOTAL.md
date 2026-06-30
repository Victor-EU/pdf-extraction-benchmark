# Fair Total — STRUCTURE-AWARE document-level information capture

> **Scores are structure-aware.** A value counts as captured only if its **binding is recoverable** — which form field it belongs to, which row/column of a table, and for a checkbox/radio whether it is **ticked** — because on these insurance forms a value under the wrong field, or a checkbox read as ticked when blank, is an *active downstream error*, worse than an omission. Correct structure described in prose still earns full credit (not a formatting test); on plain-prose pages (a cover letter, instructions) the metric reduces to ordinary content recall. The prior **content-recall** rubric (information present, ignoring binding) is preserved as a diagnostic column and in `*_content.json`. See [`../DESIGN.md`](../DESIGN.md).

Each vendor's full 7-page extraction was diffed, page by page, against a ground-truth markdown transcription (`ground_truth/GROUND_TRUTH.md`) by a blind gpt-5 judge that **credits equivalent phrasing** but requires the correct bindings to be recoverable.

**Fair total** = Σ(info_recall × page_info_weight) ÷ Σ(page_info_weight) over all pages — a true ratio of *correctly-bound information captured to total information present*, weighted by how much real content each page holds. It is NOT an average of arbitrary dimension scores.

> ◆ Gemini (and lightly the legacy Landing AI) co-authored the ground truth, so their rows are an **upper bound by construction** — reported for context, not ranked. gpt-5, LlamaParse, PyMuPDF, Tesseract and LiteParse are graded cleanly. The Landing AI row is its current **DPT-2** model (`v1/ade/parse`), re-run 2026-06-15; legacy was 87%, the change is within the n=7 judge-noise floor. See [`SPATIAL_RANKING.md`](SPATIAL_RANKING.md) for the form-spatial ranking.

## The fair total

| Vendor | **Fair total** (structure-aware) | Content recall (diagnostic) | Structure gap | Unsupported (fidelity) |
|---|---:|---:|---:|---:|
| Mistral OCR 4 | **92%** | 94% | −1 | 8% |
| Pulse (Ultra 2) | **90%** | 89% | +1 | 4% |
| gpt-5 (image) | **80%** | 79% | +1 | 11% |
| LiteParse | **56%** | 76% | −20 | 23% |
| PyMuPDF | **49%** | 71% | −23 | 7% |
| Tesseract | **44%** | 59% | −15 | 16% |
| LlamaParse | **31%** | 39% | −7 | 5% |
| Gemini 3.5 Flash ◆ | **99%** | 98% | 0 | 0% |
| Landing AI ◆ | **84%** | 88% | −4 | 14% |

> **Structure gap** = content recall − structure-aware fair total = the share of a vendor's apparent capture that does NOT survive a binding check. A large gap (PyMuPDF, Tesseract) marks a tool that recovers characters but loses structure; a small gap marks downstream-usable output. **Unsupported** now counts actively wrong bindings (a value under the wrong key) as contradictions.

## Fair total by page category (structure-aware)

| Vendor | Text | Form | Table | Mixed |
|---|---:|---:|---:|---:|
| Mistral OCR 4 | 90% | 91% | 98% | 92% |
| Pulse (Ultra 2) | 97% | 89% | 95% | 88% |
| gpt-5 (image) | 97% | 65% | 100% | 88% |
| LiteParse | 95% | 51% | 55% | 50% |
| PyMuPDF | 99% | 29% | 35% | 66% |
| Tesseract | 88% | 27% | 40% | 57% |
| LlamaParse | 0% | 31% | 60% | 28% |
| Gemini 3.5 Flash ◆ | 99% | 98% | 100% | 99% |
| Landing AI ◆ | 95% | 72% | 90% | 96% |

