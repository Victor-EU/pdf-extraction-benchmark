# Results by document genre

> **Additional analysis (2026-06-14).** The corpus's three PDFs are three different document *genres*, with very different content profiles:

> | Doc | Genre | Pages | Dominant content |
> |---|---|---:|---|
> | **Alpha** | Consulting report (French) | 156 | tables (58) + charts (34) |
> | **IAR** | Public annual report | 310 | prose (116 Text + 73 Mixed) + tables (54) |
> | **SOTER** | M&A information memorandum | 133 | charts/diagrams (80 = 60% of pages) |

All numbers are the **structure-aware fair total** (`Σ recall×weight / Σ weight`), re-aggregated from the **canonical** per-page judge scores — a value counts only if its binding (row/column/node) is recoverable (see [`../STRUCTURE_AWARE_SCORING.md`](../STRUCTURE_AWARE_SCORING.md)). gpt-5 rows are ◆ upper-bound (transcriber=judge family); read them for context, not rank. Reproduce: `python3 scripts/by_document.py`.

## What the per-document slice reveals

*(Numbers are **structure-aware** (bindings must be recoverable). Findings read off the
**gpt-5 judge** — the discriminating one. The Gemini judge compresses the structure-preserving
vendors into 93–96 but separates PyMuPDF/Tesseract identically; both tables are below.)*

**1. The annual report is the easy genre; the M&A memo is the great separator — even more so
under structure-aware scoring.** Every vendor peaks **on IAR** (born-digital prose + clean
labelled tables) and bottoms **on SOTER** (60% chart/diagram pages). On IAR the structure-
preserving vendors converge in a ~1 pp band (Gemini Flash 94, LlamaParse 94, Landing AI 93); on
SOTER they spread 9 pp (Flash 85 → LlamaParse 76) and the full field spreads **47 pp** (down to
PyMuPDF 59, Tesseract 38). **Benchmark only on annual reports and you'd wrongly conclude all
vendors are equivalent.**

**2. Gemini 3.5 Flash wins on all three genres** (83 Alpha / 94 IAR / 85 SOTER), with its widest
lead on the chart-heavy memo — the strongest binding-preserving chart reader. Safe default
regardless of document type.

**3. LlamaParse (agentic) is genre-sensitive.** Tied #1 on the annual report (94) and solid on the
French consulting deck (80), but it slips to **76 on the M&A memo** — its chart reading is good,
not best, so the chart-heavy genre is its relatively weak document.

**4. PyMuPDF drops to a clearly lower tier on every genre once structure is scored** (61 / 77 / 59).
The content-recall inflation is gone: on SOTER it **no longer edges Landing AI — it now trails it
badly (59 vs 78)**, because the chart-heavy memo is exactly where PyMuPDF's character dump loses
the most structure. Its cover cliff in the deck genres persists (Alpha 21, SOTER 23 vs IAR 77 on
text-rich annual-report covers). PyMuPDF remains a cheap, useful *text + born-digital-table* first
pass, but the per-doc numbers now reflect downstream usability, not token presence. See
[`../STRUCTURE_AWARE_SCORING.md`](../STRUCTURE_AWARE_SCORING.md), `AUDIT_PYMUPDF_STRUCTURE.md`.

**5. "Tables are solved" holds only for annual-report tables.** IAR tables score 93–95 across the
structure-preserving vendors (PyMuPDF 81), but the **French consulting deck's tables (Alpha) are
materially harder** — Gemini Flash 79, Landing AI 78, LlamaParse 76, PyMuPDF 62 — denser,
multi-header, French-language tables. Genre, not just element type, drives table difficulty.

**6. Tesseract degrades on every genre and worst on the chart memo** (50 / 60 / 38). A
scanned-document floor, not a born-digital option, in any genre.

**7. LiteParse (run-llama OSS) is a text-layer tool that scores *below* PyMuPDF once structure is
priced in** (55 Alpha / 72 IAR / 51 SOTER → 62 corpus, vs PyMuPDF 68). It is the open-sourced core
of LlamaParse minus the VLM layer, so like PyMuPDF/Tesseract it is **vision-blind** (0 figure
descriptions) and follows the same genre shape — best on the annual report, worst on the chart memo.
The twist: its heuristic "grid-projection" markdown emits far more table/heading *shape* than
PyMuPDF (table-presence 81% vs 57%) and it actually **beats PyMuPDF on plain-text and image/photo
pages** (Text 85 vs 80, Image 54 vs 28), but it **loses on every structured category** (Table 60 vs
71, Chart 45 vs 54, Mixed 71 vs 79): on dense multi-column pages the projection merges adjacent
columns into a jumble whose row/column bindings are unrecoverable, so the table-shaped output earns
no structure credit. Its structure gap (−18, content 80 → structure 62) is the **largest of any
vendor** — it captures the characters but loses the most structure relative to what it captured.
Verdict: a fast, local, Apache-2.0 *text-and-prose* first pass, but on finance/M&A tables and charts
PyMuPDF+fitz's native table extractor is the stronger free baseline, and any vision tool is a tier
above. See [`../LITEPARSE_ADD.md`](../LITEPARSE_ADD.md).


## 1. Fair-total content recall, by document


### gpt-5 judge

| Vendor | Alpha (consulting, FR) | IAR (annual report) | SOTER (M&A memo) | Corpus |
|---|---:|---:|---:|---:|
| Gemini 3.5 Flash | 83 | 94 | 85 | **89** |
| Gemini 3.1 Flash-Lite | 81 | 93 | 78 | **86** |
| LlamaParse (agentic) | 80 | 94 | 76 | **86** |
| Landing AI | 81 | 93 | 78 | **86** |
| PyMuPDF | 61 | 77 | 59 | **68** |
| LiteParse | 55 | 72 | 51 | **62** |
| Tesseract | 50 | 60 | 38 | **52** |
| gpt-5 file ◆ | 82 | 92 | 82 | **87** |
| gpt-5 image ◆ | 83 | 94 | 81 | **88** |

### Gemini judge

| Vendor | Alpha (consulting, FR) | IAR (annual report) | SOTER (M&A memo) | Corpus |
|---|---:|---:|---:|---:|
| Gemini 3.5 Flash | 94 | 98 | 94 | **96** |
| Gemini 3.1 Flash-Lite | 92 | 97 | 89 | **94** |
| LlamaParse (agentic) | 93 | 98 | 92 | **95** |
| Landing AI | 92 | 97 | 90 | **94** |
| PyMuPDF | 65 | 72 | 62 | **68** |
| LiteParse | 61 | 71 | 59 | **65** |
| Tesseract | 62 | 76 | 54 | **67** |
| gpt-5 file ◆ | 93 | 97 | 94 | **95** |
| gpt-5 image ◆ | 92 | 99 | 94 | **96** |


## 2. Fair-total content recall, by category within each document

> Column header `Cat (n)` = page support for that category in that document. Small-support cells (e.g. Image/Photo = 1 page) are anecdote, not signal.


## gpt-5 judge — fair-total by category, per document


### Alpha — Consulting report (FR) (156 pp)

| Vendor | Text (25) | Table (58) | Chart/Diagram (34) | Mixed (24) | Cover/Divider (14) | Image/Photo (1) | Doc |
|---|---|---|---|---|---|---|---|
| Gemini 3.5 Flash | 89 | 79 | 83 | 91 | 87 | 80 | **83** |
| Gemini 3.1 Flash-Lite | 89 | 77 | 78 | 88 | 85 | 65 | **81** |
| LlamaParse (agentic) | 92 | 76 | 77 | 88 | 74 | 30 | **80** |
| Landing AI | 91 | 78 | 75 | 88 | 88 | 95 | **81** |
| PyMuPDF | 85 | 62 | 44 | 77 | 21 | 20 | **61** |
| LiteParse | 78 | 55 | 38 | 73 | 22 | 55 | **55** |
| Tesseract | 75 | 51 | 29 | 65 | 22 | 35 | **50** |
| gpt-5 file ◆ | 93 | 75 | 82 | 92 | 90 | 75 | **82** |
| gpt-5 image ◆ | 93 | 76 | 83 | 92 | 92 | 90 | **83** |

### IAR — Public annual report (310 pp)

| Vendor | Text (116) | Table (54) | Chart/Diagram (38) | Mixed (73) | Cover/Divider (29) | Doc |
|---|---|---|---|---|---|---|
| Gemini 3.5 Flash | 97 | 95 | 90 | 94 | 90 | **94** |
| Gemini 3.1 Flash-Lite | 95 | 93 | 88 | 91 | 91 | **93** |
| LlamaParse (agentic) | 96 | 94 | 87 | 94 | 84 | **94** |
| Landing AI | 96 | 94 | 85 | 93 | 85 | **93** |
| PyMuPDF | 79 | 81 | 63 | 80 | 77 | **77** |
| LiteParse | 87 | 64 | 47 | 71 | 77 | **72** |
| Tesseract | 79 | 50 | 39 | 57 | 43 | **60** |
| gpt-5 file ◆ | 95 | 91 | 87 | 93 | 94 | **92** |
| gpt-5 image ◆ | 97 | 93 | 89 | 94 | 94 | **94** |

### SOTER — M&A info memorandum (133 pp)

| Vendor | Text (8) | Table (16) | Chart/Diagram (80) | Mixed (16) | Cover/Divider (12) | Image/Photo (1) | Doc |
|---|---|---|---|---|---|---|---|
| Gemini 3.5 Flash | 98 | 92 | 82 | 92 | 67 | 90 | **85** |
| Gemini 3.1 Flash-Lite | 95 | 88 | 74 | 83 | 71 | 80 | **78** |
| LlamaParse (agentic) | 96 | 86 | 72 | 87 | 63 | 90 | **76** |
| Landing AI | 93 | 84 | 76 | 83 | 69 | 60 | **78** |
| PyMuPDF | 79 | 68 | 54 | 76 | 23 | 60 | **59** |
| LiteParse | 81 | 63 | 46 | 68 | 17 | 50 | **51** |
| Tesseract | 79 | 44 | 32 | 56 | 12 | 45 | **38** |
| gpt-5 file ◆ | 96 | 85 | 80 | 85 | 76 | 95 | **82** |
| gpt-5 image ◆ | 95 | 87 | 79 | 84 | 87 | 90 | **81** |

## Gemini judge — fair-total by category, per document


### Alpha — Consulting report (FR) (156 pp)

| Vendor | Text (25) | Table (58) | Chart/Diagram (34) | Mixed (24) | Cover/Divider (14) | Image/Photo (1) | Doc |
|---|---|---|---|---|---|---|---|
| Gemini 3.5 Flash | 94 | 92 | 96 | 97 | 98 | 98 | **94** |
| Gemini 3.1 Flash-Lite | 94 | 90 | 93 | 96 | 96 | 90 | **92** |
| LlamaParse (agentic) | 95 | 91 | 94 | 96 | 89 | 90 | **93** |
| Landing AI | 95 | 89 | 93 | 94 | 97 | 95 | **92** |
| PyMuPDF | 84 | 65 | 51 | 76 | 38 | 70 | **65** |
| LiteParse | 83 | 60 | 45 | 74 | 38 | 80 | **61** |
| Tesseract | 79 | 64 | 45 | 75 | 42 | 65 | **62** |
| gpt-5 file ◆ | 97 | 88 | 97 | 95 | 100 | 95 | **93** |
| gpt-5 image ◆ | 97 | 87 | 95 | 97 | 100 | 95 | **92** |

### IAR — Public annual report (310 pp)

| Vendor | Text (116) | Table (54) | Chart/Diagram (38) | Mixed (73) | Cover/Divider (29) | Doc |
|---|---|---|---|---|---|---|
| Gemini 3.5 Flash | 98 | 98 | 97 | 99 | 98 | **98** |
| Gemini 3.1 Flash-Lite | 98 | 97 | 96 | 98 | 96 | **97** |
| LlamaParse (agentic) | 98 | 98 | 96 | 99 | 89 | **98** |
| Landing AI | 99 | 97 | 94 | 97 | 92 | **97** |
| PyMuPDF | 75 | 68 | 66 | 74 | 82 | **72** |
| LiteParse | 87 | 54 | 57 | 71 | 78 | **71** |
| Tesseract | 89 | 75 | 58 | 73 | 55 | **76** |
| gpt-5 file ◆ | 97 | 96 | 96 | 98 | 99 | **97** |
| gpt-5 image ◆ | 99 | 98 | 97 | 99 | 99 | **99** |

### SOTER — M&A info memorandum (133 pp)

| Vendor | Text (8) | Table (16) | Chart/Diagram (80) | Mixed (16) | Cover/Divider (12) | Image/Photo (1) | Doc |
|---|---|---|---|---|---|---|---|
| Gemini 3.5 Flash | 100 | 94 | 94 | 95 | 91 | 95 | **94** |
| Gemini 3.1 Flash-Lite | 98 | 90 | 87 | 93 | 92 | 80 | **89** |
| LlamaParse (agentic) | 99 | 93 | 90 | 95 | 89 | 95 | **92** |
| Landing AI | 95 | 91 | 89 | 91 | 89 | 90 | **90** |
| PyMuPDF | 78 | 63 | 59 | 73 | 46 | 60 | **62** |
| LiteParse | 82 | 74 | 54 | 71 | 34 | 35 | **59** |
| Tesseract | 86 | 64 | 48 | 66 | 30 | 55 | **54** |
| gpt-5 file ◆ | 99 | 92 | 94 | 95 | 94 | 100 | **94** |
| gpt-5 image ◆ | 99 | 93 | 94 | 95 | 98 | 100 | **94** |
