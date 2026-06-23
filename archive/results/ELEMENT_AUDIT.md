# Element-level audit — which vendor is good at what (v2 GT)

Every page's ground truth was decomposed into typed content elements (Stage A); each vendor was then graded **element by element** (Stage B, blind). Scores are aggregated BY ELEMENT TYPE across all 599 pages and salience-weighted, so a chart is judged as a chart wherever it appears — no page-bucket or document confound. gpt-5 rows (◆) are upper bounds (built the GT).

**recall** = % of that element's information conveyed · **fidelity** = 100−invented/contradicted · **coverage** = % of those elements captured at all (recall≥50) · **n** = element count.

**Elements per type (n):** Data tables 355, Charts/graphs (with data) 292, Diagrams/flows/maps 170, KPI / metric callouts 108, Narrative prose & bullets 1726, Titles & headings 1565, Footnotes / sources / logos (chrome) 1913

## Headline — best clean vendor per element type

| Element type | n | Winner (clean) | recall | Runner-up | gap |
|---|---:|---|---:|---|---:|
| Data tables | 355 | **LlamaParse** | 97% | Gemini 3.5 Flash | +0 |
| Charts/graphs (with data) | 292 | **Gemini 3.5 Flash** | 90% | Gemini 3.1 Flash-Lite | +4 |
| Diagrams/flows/maps | 170 | **Gemini 3.5 Flash** | 92% | Landing AI | +3 |
| KPI / metric callouts | 108 | **Gemini 3.5 Flash** | 100% | PyMuPDF | +0 |
| Narrative prose & bullets | 1726 | **Gemini 3.5 Flash** | 100% | LlamaParse | +0 |
| Titles & headings | 1565 | **Gemini 3.5 Flash** | 100% | LlamaParse | +0 |
| Footnotes / sources / logos (chrome) | 1913 | **Gemini 3.5 Flash** | 91% | Gemini 3.1 Flash-Lite | +2 |

## Data tables  (n=355)

| Vendor | recall | fidelity | coverage |
|---|---:|---:|---:|
| LlamaParse | 97% | 97% | 99% |
| Gemini 3.5 Flash | 97% | 97% | 99% |
| Gemini 3.1 Flash-Lite | 96% | 97% | 99% |
| gpt-5 (file) ◆ | 95% | 96% | 98% |
| gpt-5 (image) ◆ | 95% | 96% | 98% |
| Landing AI | 93% | 95% | 97% |
| PyMuPDF | 93% | 97% | 97% |
| Tesseract | 69% | 78% | 79% |

_recall by document:_ Alpha-deck: llam 94%, gemi 93%, gemi 91% · AnnualRpt: llam 99%, gemi 99%, gemi 99% · SOTER-deck: gemi 97%, gemi 95%, llam 94%

## Charts/graphs (with data)  (n=292)

| Vendor | recall | fidelity | coverage |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 90% | 91% | 96% |
| gpt-5 (file) ◆ | 89% | 90% | 96% |
| gpt-5 (image) ◆ | 88% | 89% | 95% |
| Gemini 3.1 Flash-Lite | 86% | 92% | 93% |
| Landing AI | 85% | 88% | 92% |
| LlamaParse | 83% | 88% | 93% |
| PyMuPDF | 83% | 98% | 89% |
| Tesseract | 41% | 90% | 40% |

_recall by document:_ Alpha-deck: gemi 90%, land 86%, gemi 86% · AnnualRpt: gemi 95%, gemi 92%, llam 90% · SOTER-deck: gemi 88%, pymu 84%, gemi 84%

## Diagrams/flows/maps  (n=170)

| Vendor | recall | fidelity | coverage |
|---|---:|---:|---:|
| gpt-5 (image) ◆ | 92% | 97% | 96% |
| Gemini 3.5 Flash | 92% | 96% | 94% |
| gpt-5 (file) ◆ | 89% | 97% | 89% |
| Landing AI | 89% | 95% | 94% |
| Gemini 3.1 Flash-Lite | 87% | 98% | 92% |
| LlamaParse | 83% | 96% | 86% |
| PyMuPDF | 50% | 99% | 42% |
| Tesseract | 45% | 95% | 39% |

_recall by document:_ Alpha-deck: land 85%, gemi 80%, gemi 79% · AnnualRpt: gemi 96%, gemi 93%, land 88% · SOTER-deck: gemi 94%, land 90%, gemi 87%

## KPI / metric callouts  (n=108)

| Vendor | recall | fidelity | coverage |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 100% | 100% | 100% |
| PyMuPDF | 100% | 100% | 100% |
| gpt-5 (image) ◆ | 100% | 99% | 100% |
| gpt-5 (file) ◆ | 100% | 100% | 99% |
| Gemini 3.1 Flash-Lite | 98% | 100% | 98% |
| Landing AI | 98% | 99% | 97% |
| LlamaParse | 95% | 100% | 94% |
| Tesseract | 81% | 98% | 83% |

_recall by document:_ Alpha-deck: gemi 100%, gemi 100%, land 98% · AnnualRpt: gemi 100%, land 100%, pymu 100% · SOTER-deck: gemi 100%, pymu 100%, gemi 96%

## Narrative prose & bullets  (n=1726)

| Vendor | recall | fidelity | coverage |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 100% | 100% | 100% |
| LlamaParse | 100% | 100% | 100% |
| gpt-5 (image) ◆ | 99% | 100% | 100% |
| Gemini 3.1 Flash-Lite | 99% | 100% | 99% |
| Landing AI | 99% | 100% | 99% |
| gpt-5 (file) ◆ | 98% | 100% | 99% |
| PyMuPDF | 97% | 100% | 97% |
| Tesseract | 96% | 98% | 98% |

_recall by document:_ Alpha-deck: gemi 99%, gemi 99%, llam 99% · AnnualRpt: llam 100%, gemi 100%, land 99% · SOTER-deck: gemi 100%, llam 99%, pymu 99%

## Titles & headings  (n=1565)

| Vendor | recall | fidelity | coverage |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 100% | 100% | 100% |
| gpt-5 (file) ◆ | 100% | 100% | 100% |
| LlamaParse | 100% | 100% | 100% |
| gpt-5 (image) ◆ | 100% | 100% | 100% |
| Gemini 3.1 Flash-Lite | 99% | 100% | 98% |
| PyMuPDF | 97% | 100% | 97% |
| Landing AI | 96% | 100% | 96% |
| Tesseract | 92% | 99% | 94% |

_recall by document:_ Alpha-deck: llam 100%, pymu 100%, gemi 99% · AnnualRpt: gemi 100%, llam 99%, gemi 99% · SOTER-deck: gemi 100%, pymu 100%, llam 99%

## Footnotes / sources / logos (chrome)  (n=1913)

| Vendor | recall | fidelity | coverage |
|---|---:|---:|---:|
| gpt-5 (file) ◆ | 92% | 100% | 93% |
| gpt-5 (image) ◆ | 91% | 99% | 94% |
| Gemini 3.5 Flash | 91% | 99% | 93% |
| Gemini 3.1 Flash-Lite | 88% | 100% | 91% |
| LlamaParse | 87% | 100% | 89% |
| Landing AI | 87% | 99% | 90% |
| PyMuPDF | 65% | 100% | 65% |
| Tesseract | 52% | 98% | 55% |

_recall by document:_ Alpha-deck: gemi 95%, llam 95%, land 94% · AnnualRpt: gemi 86%, gemi 85%, llam 80% · SOTER-deck: gemi 95%, land 95%, llam 92%

## Per-vendor profile (clean recall by type)

| Vendor | Data tables | Charts | Diagrams | KPI | Narrative prose & bullets | Titles & headings | Footnotes |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemini 3.5 Flash | 97% | 90% | 92% | 100% | 100% | 100% | 91% |
| Gemini 3.1 Flash-Lite | 96% | 86% | 87% | 98% | 99% | 99% | 88% |
| Landing AI | 93% | 85% | 89% | 98% | 99% | 96% | 87% |
| PyMuPDF | 93% | 83% | 50% | 100% | 97% | 97% | 65% |
| LlamaParse | 97% | 83% | 83% | 95% | 100% | 100% | 87% |
| Tesseract | 69% | 41% | 45% | 81% | 96% | 92% | 52% |
| gpt-5 (image) ◆ | 95% | 88% | 92% | 100% | 99% | 100% | 91% |
| gpt-5 (file) ◆ | 95% | 89% | 89% | 100% | 98% | 100% | 92% |


---

## Truncation correction (2026-06-13)

These numbers are the **corrected, no-truncation run**. The original judge truncated each vendor's per-page text at 6,000 chars (`VEND_CAP`), which clipped only Landing AI on 145 pages (24% — its output is 2× longer and its figure prose sits at the page end). Re-judging at a 16,000-char cap (zero truncation) raised Landing AI's KPI 84→98, charts 77→85, diagrams 85→89, tables 91→93; every other vendor moved ≤1 point and **no ranking changed**. Full trail: `AUDIT_VEND_CAP.md`.

## Significance — bootstrap 95% CI on the clean winner's lead

Charts **+3.8 [+2.1,+5.6]**, diagrams **+3.4 [+0.4,+6.8]**, prose **+0.8 [+0.4,+1.2]**, titles **+0.8 [+0.3,+1.3]**, chrome **+2.5 [+1.4,+3.6]** are real wins for Gemini Flash. **Tables +0.2 [−0.5,+0.9]** and **KPI +0.4 [0.0,+1.0]** are statistical **ties** — report them as ties, not wins.

## Hand-audit of the scores (vs GT) — are these numbers real?

The highest-divergence elements per data type were read by hand (GT element key_facts vs each vendor's actual page text, against the page image). The scores are faithful, with one documented judge limitation:

- **Data tables — faithful.** On born-digital tables PyMuPDF reproduces every value exactly from the text layer (recall 100); Tesseract scores recall ~30 with *wrong ~70* — it emits genuinely wrong numbers, matching its low table fidelity. The PyMuPDF–Landing AI table gap (93 vs 93) is a tie.
- **Charts — faithful, mechanism = text layer.** PyMuPDF earns chart credit because born-digital decks carry the data labels in the text layer (verified on SOTER quarterly-EBITDA values). It captures chart NUMBERS, not chart geometry.
- **Diagrams — faithful at the extremes, one caveat (verified vs page image).** Visual-only diagrams (e.g. IAR p139 six-domain security graphic, labels rendered inside the image) → PyMuPDF recall 0, correctly (labels absent from its text layer; confirmed against the rendered page). Text-dense org charts (SOTER p92) → PyMuPDF recall 100 even though the *reporting structure is scrambled* into floating tokens. The paraphrase-tolerant judge under-penalizes lost diagram STRUCTURE when all tokens are present, so PyMuPDF's true diagram score is if anything **below** the reported 50% — i.e. the vision-model lead on diagrams is conservative, never inflated.

## Cross-family confirmation (gpt-5 judge vs Gemini judge)

The same fixed element inventory was re-scored by a non-OpenAI judge (gemini-3.5-flash, $15.81), also at the corrected 16,000-char cap. Per-type winners agree 5/7. The two that differ — **diagrams** (gpt-5 → Gemini Flash 92; Gemini judge → Landing AI 95) and **KPIs** (Gemini Flash / Landing AI / PyMuPDF all 98–100) — are **ties at the top of the vision tier**, not rank reversals: both judges put the figure-reading tier (Gemini/gpt-5/Landing AI/**LlamaParse agentic**, ~83–95) far above the *pure text-layer* parsers (PyMuPDF, Tesseract ~45–50) on diagrams, and both rank Gemini Flash #1 on tables, charts, narrative, titles and chrome. The Gemini judge is uniformly more lenient (Tesseract tables +15, chrome +14) without reordering the strong tier. Full table: `results/ELEMENT_JUDGES.md`.

## LlamaParse tier correction (2026-06-13) — these numbers are AGENTIC tier

LlamaParse is scored here at its **`agentic` tier (its most capable mode)**, re-run after we found the original benchmark had used the middle `accurate` tier, which silently dropped whole born-digital pages. Switching to agentic lifts LlamaParse on every element type — **charts 56→83, diagrams 46→83, tables 79→97, footnotes/sources 61→87, prose 84→100** (gpt-5 judge) — moving it from a text-layer specialist to a top-tier all-rounder (element-ALL 78→95). Agentic runs an LVM loop, so unlike PyMuPDF/Tesseract it actually *reads* charts and diagrams. Every other vendor moved ≤0.3 pp on the re-judge. Full trail: `AUDIT_LLAMAPARSE_MODE.md`.
