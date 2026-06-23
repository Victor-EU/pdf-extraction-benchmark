# Which vendor is good at what — element-level verdict

> **Consistent with the structure-aware headline (2026-06-14).** This element-level eval already
> prices structure per element type (e.g. PyMuPDF diagrams 50 vs charts 83), which is *why* it
> foresaw the headline change: the tools weak here on diagrams/figures are exactly the ones that drop
> when the fair total goes structure-aware (PyMuPDF 84→68). See [`../STRUCTURE_AWARE_SCORING.md`](../STRUCTURE_AWARE_SCORING.md).

Built by decomposing all 599 ground-truth pages into **6,129 typed content elements** (Stage A) and
grading every vendor **element by element**, blind (Stage B). Aggregated BY ELEMENT TYPE across the
whole corpus and salience-weighted — so a chart is scored as a chart wherever it sits, removing the
page-bucket and document-mix confounds of the page-category table. Verified four ways: independent
re-derivation from the raw judge JSON, bootstrap confidence intervals, a hand-audit of the
highest-divergence elements vs the GT, and a cross-family Gemini judge. gpt-5 rows are an upper bound
(built the GT). Element judge $24.65 + Gemini confirm $15.81.

> **Corrected 2026-06-13 (two fixes).** (1) A 6,000-char cap on each vendor's per-page text (`VEND_CAP`)
> was truncating Landing AI on 145 pages (24%) — only Landing AI, whose output is 2× longer. Re-judged at a
> no-truncation cap under both families; its figure/KPI scores rose 2–13 points (`AUDIT_VEND_CAP.md`).
> (2) **LlamaParse was re-run at its most capable `agentic` tier** (the original used the middle `accurate`
> tier, which silently dropped whole pages). Its element scores rose on every type — charts 56→83,
> diagrams 46→83, tables 79→97 — moving it from a text-layer specialist to a top all-rounder. Every other
> vendor moved ≤0.3 pp. Full trail: `AUDIT_LLAMAPARSE_MODE.md`.

## Recall by element type (clean vendors), gpt-5 judge

| Vendor | Tables (355) | Charts (292) | Diagrams (170) | KPI (108) | Prose (1726) | Titles (1565) | Chrome (1913) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Gemini 3.5 Flash** | **97** | **90** | **92** | **100** | **100** | **100** | **91** |
| Gemini 3.1 Flash-Lite | 96 | 86 | 87 | 98 | 99 | 99 | 88 |
| **LlamaParse** (agentic) | **97** | 83 | 83 | 95 | 100 | 100 | 87 |
| Landing AI | 93 | 85 | 89 | 98 | 99 | 96 | 87 |
| PyMuPDF | 93 | 83 | 50 | 100 | 97 | 97 | 65 |
| Tesseract | 69 | 41 | 45 | 81 | 96 | 92 | 52 |
| _gpt-5 (image) ◆_ | _95_ | _88_ | _92_ | _100_ | _99_ | _100_ | _91_ |
| _gpt-5 (file) ◆_ | _95_ | _89_ | _89_ | _100_ | _98_ | _100_ | _92_ |

(n = element count. Recall = % of that element's information conveyed, paraphrase credited.)

**Statistical significance (bootstrap 95% CI on the clean winner's lead over the runner-up):**
charts **+3.8 [+2.1,+5.6]**, diagrams **+3.4 [+0.4,+6.8]**, prose **+0.8 [+0.4,+1.2]**,
titles **+0.8 [+0.3,+1.3]**, chrome **+2.5 [+1.4,+3.6]** are real wins for Gemini Flash;
**tables (+0.2 [−0.5,+0.9])** and **KPI (+0.4 [0.0,+1.0])** are statistical **ties** at the top.

## The verdict, per vendor

- **Gemini 3.5 Flash — best generalist, wins or ties every element type.** The only vendor with no
  weak cell. Significantly best on charts, diagrams, prose, titles and chrome; tied at the top on tables
  and KPIs. If you pick one parser for mixed documents, this is it.
- **Gemini 3.1 Flash-Lite — Gemini Flash minus a few points on the hard visuals** (charts 86,
  diagrams 87). Same shape, cheaper, slightly less precise on dense figures. Neck-and-neck with Landing
  AI for the second clean slot on the holistic total.
- **Landing AI — strong across the board once its full output is read.** Tables 93, diagrams **89**
  (2nd among clean), KPI **98** and charts **85** — all materially higher than the pre-correction figures
  that had truncated its figure prose. Its genuine, non-artifact trait is **the highest unsupported/padding
  rate of any parser (17%)**: it captures more *and* asserts more. Reads image-based pages text-layer
  parsers can't.
- **PyMuPDF ($0 usage, but AGPL-licensed) — the text-layer specialist; spikiest profile.** Elite on anything whose values
  live in a born-digital text layer: tables **93**, KPI **100**, prose 97, titles 97 — and even charts
  **83**, because it recovers chart data labels verbatim. **Collapses on what is purely visual:**
  diagrams **50**, chrome **65**, and ~0 on any image-based/scanned page (no text layer). Zero
  invention (fidelity ~100). Best text-layer option when documents are born-digital and not diagram-heavy — but note **PyMuPDF is AGPL-3.0 / paid-commercial, not free for proprietary use**; for a permissive license at the same tier use **pdfplumber (MIT) / pypdf (BSD)** (see `../FINAL_REPORT.md` §6 note ¹).
- **LlamaParse (agentic) — top-tier all-rounder, no weak cell on born-digital docs.** Tables **97**
  (ties the #1 spot), prose **100**, titles **100**, and — unlike the other parsers — it *reads figures*:
  charts **83**, diagrams **83**, level with the vision tier, because the agentic tier runs an LVM loop.
  Plus exact element coordinates. Low padding (8%). **Requires the `agentic` tier** — the `accurate` tier
  scored charts 56 / diagrams 46 and is the version to avoid. (The figure-*dimension* judge under-counts
  its diagrams — 30 — because it delivers them as inline markdown not figure blocks; the element-level
  judge here, 83, is the fair number. See `AUDIT_LLAMAPARSE_MODE.md`.)
- **Tesseract (free OCR) — prose only.** Fine on rendered body text (prose 96, titles 92) but
  weak and *error-prone* on data: tables 69 with the lowest fidelity (emits wrong numbers), charts
  41, diagrams 45.

## Where the choice actually turns

| If your documents are… | Best pick | Why |
|---|---|---|
| Mixed / unknown | **Gemini 3.5 Flash** | no weak element type |
| Born-digital, table/number-heavy, budget=0 | **PyMuPDF** | tables 93 / KPI 100 / charts 83, never invents, free |
| Diagram / flowchart / map heavy | **Gemini (or gpt-5 / Landing AI / LlamaParse agentic)** | figure-reading tier 83–92; the *pure text-layer* parsers (PyMuPDF/Tesseract) ~45–50 |
| Scanned / image-based pages | **Gemini or Landing AI** | text-layer parsers return nothing there |
| Need exact element coordinates | **Landing AI** or **LlamaParse (agentic)** | the two high-quality tiers with exact boxes; LlamaParse also reads figures |
| Plain prose, budget=0 | **Tesseract** ok | prose 96, but never trust its numbers |

## Caveats (honest)
- **Diagrams & KPIs: the #1 clean spot is judge-dependent at the top.** On corrected data both judges
  agree the figure-reading tier (Gemini / Landing AI / gpt-5 / LlamaParse-agentic ≈ 83–95) towers over the
  pure text-layer parsers (PyMuPDF/Tesseract ~45–50), but
  the gpt-5 judge ranks Gemini Flash #1 on diagrams (92) while the Gemini judge ranks Landing AI #1 (95);
  on KPIs Gemini, Landing AI and PyMuPDF all sit at 98–100. Treat the top of these two types as a tie.
- **Charts: PyMuPDF vs Landing AI is judge-dependent.** gpt-5 favors PyMuPDF's raw numbers (83 vs 85
  for LA — now close); the Gemini judge favors LA's described structure. Both agree Gemini Flash wins.
- **Diagram structure is under-penalized:** a text parser that dumps a scrambled org chart with all
  labels present can score high though the reporting structure is lost — so the parser/​vision gap on
  diagrams is conservative, not inflated.
- **PyMuPDF/Tesseract recall = "is the info present," not "is it well-structured."** They emit flat
  text; downstream you must re-impose table/diagram structure.
- 3 born-digital documents (annual report + 2 decks); no scanned-document corpus beyond the few
  image-based pages inside the annual report.
