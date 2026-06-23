# PDF Extraction Benchmark

A structure-aware benchmark of **8 PDF extraction approaches** — vision LLMs, hosted document parsers, and local text-layer/OCR tools — measured on how much of a complex business document's *actual information* (text, tables, chart data, diagram structure, layout) each one recovers **with the bindings intact**.

The headline metric is the **structure-aware fair total**: a value counts only if its binding is recoverable (which row / column / series / node it belongs to). On finance/M&A/consulting documents, a number bound to the wrong row is an *active downstream error* — worse than an omission — so structure is scored, not caveated.

> **📄 Start with [`FINAL_REPORT.md`](FINAL_REPORT.md).** Methodology and bias controls are in [`DESIGN.md`](DESIGN.md).

## Headline result

Corpus: 3 finance/business PDFs, 599 pages (a French consulting deck, an English annual report, an English investor deck). `◆` = upper bound (gpt-5 built the reference the judge grades against — reported for context, not ranked).

| Rank | Vendor | Fair total (structure-aware) | Content recall | Structure gap | Cost (599pp) | Speed |
|---:|---|---:|---:|---:|---:|---:|
| 1 | **Gemini 3.5 Flash** | **89%** | 92% | −3 | $7.12 | 6.9 s/pg |
| 2 | Gemini 3.1 Flash-Lite | 86% | 90% | −4 | **$1.12** | 4.4 s/pg |
| 3 | LlamaParse (agentic) | 86% | 90% | −4 | paid | 1.3 s/pg |
| 4 | Landing AI | 81% | 87% | −6 | paid | 16.6 s/pg |
| 5 | PyMuPDF | 68% | 84% | **−16** | $0 usage¹ | **0.11 s/pg** |
| 6 | Tesseract | 52% | 64% | −12 | $0 | 1.2 s/pg |
| ◆ | gpt-5 (image) | 88% ◆ | 91% | −3 | $13.82 | 4.1 s/pg |

**Takeaways:** Gemini 3.5 Flash wins on capture at ~half gpt-5's cost; Flash-Lite is the value frontier (86% for $1.12). Structure-aware scoring sorts vendors into two classes — structure-preservers lose ≤6 pts vs raw content recall, the two pure-text-dump tools (PyMuPDF, Tesseract) lose 11–16. Speed runs *opposite* to quality (fastest tool is the weakest). See the report for the full per-category, per-document, cost, and speed breakdowns plus the four-way ground-truth validation.

¹ PyMuPDF usage is free but it is **AGPL-3.0 / paid commercial** — not free for proprietary/SaaS use. Permissive text-layer alternatives: pdfplumber (MIT), pypdf (BSD). See `FINAL_REPORT.md` §6.

## Reports

| File | What it covers |
|---|---|
| [`FINAL_REPORT.md`](FINAL_REPORT.md) | The full benchmark: headline, per-category, cost, speed, recommendations, caveats |
| [`DESIGN.md`](DESIGN.md) | Methodology, bias controls, reproducibility |
| [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md) | The canonical metric: why/how scores require recoverable bindings |
| [`GT_VALIDATION.md`](GT_VALIDATION.md) | Four-axis ground-truth validation (audit → correction → re-measure → cross-family judge) |
| [`RECONCILIATION.md`](RECONCILIATION.md) | Reconciliation with a second, independent audit |
| [`ENTERPRISE_EXTRACTION_PLAYBOOK.md`](ENTERPRISE_EXTRACTION_PLAYBOOK.md) | Practical routing/build guidance distilled from the results |
| `AUDIT_*.md` | Measurement-artifact audits (judge-input cap, LlamaParse tier, PyMuPDF structure) |
| `POC_DETERMINISTIC_SCORING.md` | Can a deterministic scorer replace the LLM judge? (partial) |
| `results/*.md` | Per-vendor scorecards and the comparison tables behind the report |

## Repository layout

```
scripts/          extraction harness + scoring/judging pipeline (Python)
results/*.md       scorecards and comparison tables
*.md               the reports (above)
.env.example       the API keys each script expects
```

## Data is not included

This repository ships the **code and findings only**. The three source PDFs, their full ground-truth transcriptions, the page-image renders, and the per-vendor reconstructions are **deliberately excluded** (`.gitignore`) because they reproduce the entire content of documents that are not cleared for public distribution. As a result the benchmark is **not runnable end-to-end from this repo as-is** — the scripts and methodology are published for inspection, reuse, and adaptation to your own corpus.

To run it on your own PDFs: drop them in `Data/`, set up `.env` from `.env.example`, and follow the pipeline described in `DESIGN.md` (render → per-vendor extract → judge → score).

## Reproducing on your own corpus

```bash
cp .env.example .env        # fill in your keys
# place your PDFs in Data/
python3 scripts/build_gt_md_v2.py     # build the ground-truth reference
python3 scripts/gemini_extract.py gemini-3.5-flash image
python3 scripts/score_fair_total.py   # structure-aware judging
```

See `DESIGN.md` for the full step list, the judge prompts, and the bias controls.

## License

[MIT](LICENSE) © 2026 Victor Zhang. The reports describe results obtained against a private corpus; the numbers are properties of that corpus and the dated vendor model versions.
