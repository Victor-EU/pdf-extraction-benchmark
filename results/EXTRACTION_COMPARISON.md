# Extraction-Quality Comparison — how completely each vendor recovers a page's information

> **⁂ The Landing AI row is the legacy pre-DPT-2 endpoint.** This element-level eval has **not** been re-run on the current `dpt-2-latest` model (only the headline fair total was; see [`../LANDINGAI_DPT2_REBENCH.md`](../LANDINGAI_DPT2_REBENCH.md)). DPT-2 raised Landing AI's structure-aware table 80→86 and chart 73→78, so treat the Landing AI numbers below as a **floor**. Every other vendor is current.

"Full extraction" = **text + tables + diagram descriptions + graph data + spatial layout** (the four dimensions Landing AI's output embodies). Scored on the 599-page corpus, segmented by the v3 page-category labels. Two metric families:
- **Objective** (vs a vendor-neutral reference = born-digital text-layer ∪ image-region OCR): content-token recall, numeric/finance recall, table emission, reading order.
- **Figure judging** (blind gpt-5 vision judge vs the page image, all 10 vendors shuffled A–J): graph-data fidelity over 123 graph pages, diagram-structure fidelity over 97 diagram pages.

## The capability matrix

| Vendor | Content recall | Numbers (finance) | Table recovery | **Graph data** | **Diagram struct** | Reading order | Coordinates | Cost (599pp) |
|---|---:|---:|---:|---:|---:|---:|:--:|---:|
| gpt-5 (image) | 97% | 96% | 90% | **85%** | **66%** | 67% | coarse | $13.82 |
| gpt-5 (file) | 97% | 97% | 91% | **84%** | **70%** | 60% | coarse | $12.54 |
| Gemini 3.5 Flash | 97% | 96% | 98% | **85%** | **91%** | 67% | coarse | $7.12 |
| Gemini 3.1 Flash-Lite | 96% | 95% | 94% | **83%** | **82%** | 67% | coarse | $1.12 |
| Landing AI | 95% | 93% | 91% | **80%** | **82%** | 63% | exact boxes | paid |
| LlamaParse | 97% | 95% | 99% | **77%** | **30%** | – | exact boxes | paid (agentic) |
| Mistral OCR 4 | 96% | 94% | 94% | **59%** | **60%** | – | exact boxes | $5/1k pages |
| Pulse (Ultra 2) | 97% | 96% | 94% | **–** | **–** | – | exact boxes | ~10 cr/pg |
| PyMuPDF | 97% | 97% | 57% | **29%** | **29%** | 90% | exact boxes | $0 |
| Tesseract | 88% | 72% | 0% | **24%** | **29%** | 68% | word boxes | $0 |
| LiteParse | 96% | 95% | 81% | **12%** | **14%** | – | exact boxes | $0 (local) |

> Reading-order is Kendall-τ vs the reference order; PyMuPDF's is inflated because the reference uses the same layout engine — read it as a capability flag, not a ranking. Coordinates column is a capability: parsers emit exact boxes; gpt-5 emits only coarse positions.

> **Table recovery** = on pages whose dominant content is a table (the 128 `Table`-labeled pages), did the vendor emit a structured table? `Mixed` pages are deliberately excluded — ~half are chart+text/infographic with no table, so requiring one there punished principled abstention (Landing AI) and rewarded layout→table over-emission (the accurate-tier LlamaParse emitted a table on every no-table Mixed page checked; agentic LlamaParse instead tabulates chart data, which is genuine capture). Landing AI is also credited when its ADE renders a photo/logo-embedded table as a `figure` chunk holding the full table data. The earlier metric (denominator = `Table`∪`Mixed`, literal `table` blocks only) is kept in `_extraction_objective.json` as `table_presence_legacy`; it scored Landing AI 56% — an artifact, not its true ~91% table recovery.

## Graph-data fidelity by category (the finance question)

| Vendor | Chart/Diagram | Mixed | overall |
|---|---:|---:|---:|
| gpt-5 (image) | 85% | 83% | 85% |
| gpt-5 (file) | 84% | 84% | 84% |
| Gemini 3.5 Flash | 85% | 86% | 85% |
| Gemini 3.1 Flash-Lite | 83% | 82% | 83% |
| Landing AI | 80% | 82% | 80% |
| LlamaParse | 76% | 80% | 77% |
| Mistral OCR 4 | 62% | 50% | 59% |
| Pulse (Ultra 2) | – | – | – |
| PyMuPDF | 29% | 28% | 29% |
| Tesseract | 24% | 24% | 24% |
| LiteParse | 12% | 13% | 12% |

## Diagram-structure fidelity by category

| Vendor | Chart/Diagram | Mixed | overall |
|---|---:|---:|---:|
| gpt-5 (image) | 69% | 58% | 66% |
| gpt-5 (file) | 76% | 55% | 70% |
| Gemini 3.5 Flash | 92% | 90% | 91% |
| Gemini 3.1 Flash-Lite | 83% | 77% | 82% |
| Landing AI | 83% | 79% | 82% |
| LlamaParse | 35% | 17% | 30% |
| Mistral OCR 4 | 65% | 48% | 60% |
| Pulse (Ultra 2) | – | – | – |
| PyMuPDF | 30% | 26% | 29% |
| Tesseract | 30% | 26% | 29% |
| LiteParse | 17% | 5% | 14% |

> **LlamaParse diagram caveat.** This figure judge reads each vendor's *figure-typed* blocks; LlamaParse (agentic) delivers its diagram content as **inline markdown prose**, not figure blocks, so this metric under-counts it (~30 here). The element-level judge, which reads LlamaParse's full markdown, scores its diagrams **83** (gpt-5) / **86** (Gemini) — see `results/ELEMENT_AUDIT.md`. Its graph-data score (77, up from 51 at the accurate tier) rises here because tabulated chart data lands in its tables. Read the element-level diagram number as the true figure capability.
> **Pulse figure caveat (shows `–` above).** Pulse (Ultra 2) was added to the headline fair total only, not this structured figure judge. In its advanced config Pulse does **not** emit per-figure blocks — its `Images[]` are bare `[Image]` placeholders and it weaves chart/diagram understanding **inline into the page markdown** (e.g. a SOTER chart's “50 billion connected devices / 26 billion / 15 years” came back as prose). The structure-aware fair total reads that full markdown, so Pulse's figure reading is measured by its **Chart-category fair total = 73%** (above Mistral's 62, below Gemini Flash's 84) — a real, no-fabrication figure score (see [`../PULSE_ADD.md`](../PULSE_ADD.md)). Running this structured judge on its empty placeholders would manufacture a misleading ~0.

## Content + numeric recall by category (objective)

**Content recall:**

| Vendor | Text | Table | Chart | Mixed | Cover | Image |
|---|---:|---:|---:|---:|---:|---:|
| gpt-5 (image) | 97% | 98% | 99% | 99% | 88% | 95% |
| gpt-5 (file) | 96% | 100% | 99% | 99% | 88% | 99% |
| Gemini 3.5 Flash | 97% | 99% | 99% | 99% | 88% | 99% |
| Gemini 3.1 Flash-Lite | 96% | 99% | 96% | 98% | 88% | 94% |
| Landing AI | 97% | 97% | 95% | 96% | 88% | 85% |
| LlamaParse | 97% | 99% | 97% | 99% | 88% | 99% |
| Mistral OCR 4 | 97% | 99% | 95% | 98% | 88% | 96% |
| Pulse (Ultra 2) | 97% | 100% | 97% | 99% | 88% | 99% |
| PyMuPDF | 96% | 100% | 99% | 99% | 84% | 99% |
| Tesseract | 94% | 90% | 89% | 91% | 62% | 85% |
| LiteParse | 97% | 96% | 98% | 97% | 80% | 98% |

**Numeric (finance) recall:**

| Vendor | Text | Table | Chart | Mixed | Cover | Image |
|---|---:|---:|---:|---:|---:|---:|
| gpt-5 (image) | 97% | 98% | 95% | 97% | 90% | 100% |
| gpt-5 (file) | 97% | 100% | 97% | 97% | 90% | 100% |
| Gemini 3.5 Flash | 96% | 99% | 95% | 98% | 90% | 100% |
| Gemini 3.1 Flash-Lite | 96% | 100% | 89% | 97% | 90% | 100% |
| Landing AI | 95% | 97% | 89% | 93% | 86% | 100% |
| LlamaParse | 97% | 100% | 89% | 96% | 90% | 100% |
| Mistral OCR 4 | 97% | 99% | 86% | 95% | 90% | 100% |
| Pulse (Ultra 2) | 97% | 99% | 93% | 97% | 90% | 100% |
| PyMuPDF | 96% | 100% | 99% | 98% | 90% | 100% |
| Tesseract | 75% | 76% | 68% | 72% | 63% | 94% |
| LiteParse | 97% | 97% | 97% | 96% | 73% | 100% |

## Notes & caveats

- **Gemini 3.5 Flash is the new overall leader on the figure dimensions** — top-tier graph-data fidelity (85%, level with gpt-5) and a commanding lead on diagram structure (91% vs gpt-5 66–70% / Landing AI 82%) — at ~half gpt-5's cost. **Gemini 3.1 Flash-Lite** roughly matches Landing AI on figures (83%/82%) for **$1.12** (12× cheaper than gpt-5). _(Figure dims = no-truncation re-judge, `AUDIT_VEND_CAP.md`.)_
- **Judge-is-gpt-5 caveat, now *strengthened*:** the blind vision judge is gpt-5, yet it scored Gemini's diagrams *above its own* (91% vs 66%) without knowing which extraction was whose. A judge favouring a competitor over itself is evidence the blind+vs-image design is not self-serving.
- **Gemini = native-vision LLM, same family as gpt-5:** coarse positions only (no element boxes), tables/figures recovered as described content. Run in `image` mode (rendered PNG) with the identical prompt+schema as gpt-5, so the comparison isolates the model. `thinkingLevel=minimal` (the analog of gpt-5 `effort=low`).
- **One degenerate page per Gemini model** (`gemini-3.5-flash`: Alpha p5; `gemini-3.1-flash-lite`: IAR p103) hit the shared 16k-output cap via runaway repetition and scored empty — gpt-5 did both in ~2k tokens. 1/599 each; aggregates unaffected. A real (small) robustness data point, not a harness artefact.

