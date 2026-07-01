# PDF Extraction Benchmark — Final Report

**Date:** 2026-06-30 (first published 2026-06-15) · **Corpus:** 3 finance/business PDFs, 599 pages · **Approaches:** 11
**Methodology:** [`DESIGN.md`](DESIGN.md) · **Headline metric:** the *structure-aware fair total* (document-level information capture where a value counts only if its binding is recoverable) · **Metric note:** [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md)

> **Vendor versions.** Each approach is run in its **most capable documented mode**: LlamaParse on its `agentic` tier ([`AUDIT_LLAMAPARSE_MODE.md`](AUDIT_LLAMAPARSE_MODE.md)) and **Landing AI on its current `v1/ade/parse` model `dpt-2-latest`** — re-benchmarked on the full corpus under both judge families on 2026-06-15 (the earlier run used Landing AI's legacy pre-DPT-2 endpoint; full trail in [`LANDINGAI_DPT2_REBENCH.md`](LANDINGAI_DPT2_REBENCH.md)). The headline fair total (§2–§3, §6) reflects DPT-2; the per-capability/element-level diagnostics (§4–§5) have not yet been re-run on DPT-2 and are flagged where they appear.

---

## 1. Executive summary

We measured how much of a complex business document's **actual information** — text, tables, chart *data*, diagram structure, layout — each of eleven extraction approaches recovers, across a 599-page corpus (a French consulting deck, an English annual report, an English investor deck). The headline is the **structure-aware fair total**: a density-weighted ratio of information captured to information present, where a value counts **only if its binding is recoverable** (which row/column/series/node it belongs to). On finance/M&A/consulting documents a number bound to the wrong row is an *active downstream error*, worse than an omission — so structure is scored, not caveated. Correct structure described in prose earns full credit; on unstructured pages the metric is plain content recall. The prior content-recall numbers are kept as a diagnostic (the **structure gap** between them is itself a vendor property). See [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md).

**The nine things that matter:**

1. **Gemini 3.5 Flash wins on structure-aware capture — 89%** — at **~half the cost of gpt-5**, with low padding (8% unsupported) and the smallest structure gap of any vendor (−3). Best quality-per-dollar of any vendor that doesn't share a family with the judge.
2. **Gemini 3.1 Flash-Lite is the value shock — 86% for $1.12.** It gives up ~3 points to its bigger sibling for **~6× less money**.
3. **Landing AI on DPT-2 joins the top tier — 86%, tied for 2nd.** Re-benchmarked on its current model (`dpt-2-latest`), Landing AI rises from 81% (legacy endpoint) to **86%** under the gpt-5 judge and 94% under Gemini — level with LlamaParse-agentic and Flash-Lite, behind only Gemini Flash. DPT-2 also **cut its padding from 17% to 11%** (no longer the highest — that is now Mistral at 19%) and **halved its structure gap (−6 → −3)**, moving it from "verbose middle tier" to a genuine structure-preserver. It is **best-in-class on Image/Photo (88%)**, strong on tables (86%), and reads charts (78%, ahead of LlamaParse). Both judge families agree, with the largest gains on the hardest genres (chart-heavy M&A memo +7, French consulting deck +7). See [`LANDINGAI_DPT2_REBENCH.md`](LANDINGAI_DPT2_REBENCH.md).
4. **Structure-aware scoring is the great separator — and it sorts vendors into two classes.** Every tool that *preserves structure* (the vision LLMs, Landing AI, agentic LlamaParse) loses ≤6 pts vs its content-recall number; the three local text-layer tools, **PyMuPDF (84→68), LiteParse (80→62) and Tesseract (64→52), lose 11–18** — identically under both independent judge families. Recovering the right characters is not the same as recovering usable information.
5. **PyMuPDF is a cheap text/table first pass, not a top-tier extractor — 68%.** Its 84% content recall was inflated by structure loss: it merges side-by-side tables and destroys relational-diagram bindings (org charts, process flows). It is still excellent value for born-digital *text + simple tables* at $0 usage, but it drops to a clear lower tier once bindings are scored (and is AGPL-licensed — note ¹). See [`AUDIT_PYMUPDF_STRUCTURE.md`](AUDIT_PYMUPDF_STRUCTURE.md).
6. **The high-quality tier is now a five-way cluster (86–89%), three of them coordinate-grade.** Gemini Flash (89) leads; Landing AI, Gemini Flash-Lite, LlamaParse-agentic and **Pulse** all sit at 86. Among them **Landing AI, LlamaParse-agentic and Pulse emit exact element bounding boxes** — the layout-provenance capability no LLM offers. **Tesseract (52%)** is a scanned-document last resort.
7. **LiteParse (run-llama's OSS) scores *below* PyMuPDF — 62% — despite being the open-sourced core of LlamaParse.** It ships *minus* the VLM layer, so like PyMuPDF/Tesseract it is **vision-blind** (worst figure reader of all ten: graph-data 12%, diagram-structure 14%). Its heuristic "grid-projection" markdown emits *more* table/heading shape than PyMuPDF (table-presence 81% vs 57%) and even **beats PyMuPDF on plain text and image/photo pages**, but on dense multi-column finance pages the projection **merges adjacent columns into a jumble whose bindings are unrecoverable**, so the table-shaped output earns no structure credit. Result: the **largest structure gap of any vendor (−18)** and a fast, local, Apache-2.0 *text-and-prose* first pass that is *not* a structured-data extractor — for finance tables/charts, PyMuPDF+fitz's native table finder is the stronger free baseline. See [`LITEPARSE_ADD.md`](LITEPARSE_ADD.md).
8. **Mistral OCR 4 (most advanced config) is a strong text/table extractor and a real figure reader — 80%, 6th among real vendors (just below the four-vendor 86 tier) — but the only vendor whose error mode is *fabrication*.** Run with `mistral-ocr-4-0` + the Document-AI per-image annotation layer that *describes* charts, it preserves structure (gap −4, like the vision tier, not the text-layer tools), is near-top on text (96%, behind only Pulse's 97), is 2nd-best on image/photo (86%, behind Landing AI's 88%), and genuinely reads charts (chart-data 59 vs text-layer ~12–29) — a structure-aware confirmation that OCR 4 *can* approach the agentic parsers on figures. **But it carries by far the highest unsupported rate of any vendor (19% gpt-5; next is Tesseract 15%):** its annotation layer **invents** content on graphics it can't parse — on one page of certification logos it fabricated a generic flowchart and a Portuguese document-management UI. The strict gpt-5 judge prices this; the lenient Gemini judge (7%) does not — which is why both families are scored. Adopt it for text/tables and cheap chart reach (~$3/599pp), but gate figure-derived claims behind its confidence scores. See [`MISTRAL_ADD.md`](MISTRAL_ADD.md).
9. **Pulse (Ultra 2, most advanced config) is the cleanest vision vendor — 86%, and the *lowest fabrication of any* (5% unsupported) — the exact inverse of Mistral.** Run with `pulse-ultra-2` + `refine` + figure description, it ties into the 86% high-quality cluster (top of the field on Text 97 / Table 90, ties best on Mixed 93), preserves structure (gap −4), and is a real chart reader (Chart-category 73, above Mistral's 62) — it writes chart data *inline into the page markdown* rather than a separate figure channel, so its figure reading is scored by the headline fair total, not the structured figure eval (which it was excluded from to avoid a misleading ≈0 on its empty image placeholders; measured instead by Chart-73). Its distinguishing trait is **fidelity**: **5.8% unsupported (gpt-5), 1.5% (Gemini)** (weight-weighted means; the §2 table's 5% is the unweighted page mean of the same data) — below every vision tool and level with the most conservative text-dumper — putting it furthest-left in the "safe & accurate" corner. The apples-to-apples 11-up run places it at the cluster's *lower edge*, so the headline is the trust column, not the rank. Its cost is latency (`refine` ~19 s/pg median). Across the sibling insurance benchmark it is likewise the low-fabrication standout (clean #2) — the steady inverse of Mistral's genre-swing. See [`PULSE_ADD.md`](PULSE_ADD.md).

> **Note on gpt-5 (◆).** gpt-5 built the transcription the judge grades against, so its rows (88%/87% structure-aware) are an **upper bound by construction** — reported for context, not ranked. Even so, **Gemini Flash edges it (89% vs 88%)** *despite* the twin advantage — strong evidence the residual bias is mild and the clean ranking is trustworthy (validated four ways in §9, and the structure change reproduces identically under a non-OpenAI judge).

> **Operational note — speed.** Per-page extraction latency spans **~245×**: PyMuPDF **0.11 s/page** (local) to gpt-5 **~27 s/page** (full-markdown extraction, both input modes). The Gemini vision tier clusters at **4–7 s/page** (Flash-Lite 4.4, Flash 6.9); the slow end is gpt-5 (27.1 image / 26.9 file) and the **document-AI parsers** — Landing AI (21.5, a harness artifact) and **Pulse (18.8, the genuine cost of its `refine` re-OCR pass)**. Latency does *not* track capture on this corpus (the fastest tools sit in the weakest class). Full table and the measurement caveats are in §6.

---

## 2. The headline — structure-aware fair total

> *How much of the document's real information did this vendor convey **with the bindings intact**?* Each vendor's full 599-page extraction was diffed page-by-page against `ground_truth/GROUND_TRUTH.md` by a blind gpt-5 judge that **credits equivalent phrasing** (a chart described in different-but-correct words, with the same numbers *and the same value↔row/series/node bindings*, counts as captured) but scores tokens whose bindings are destroyed as un-recalled. The total is **Σ(info_recall × page_info_weight) ÷ Σ(page_info_weight)**. Not a dimension average; not token overlap. The **content recall** column is the prior rubric (presence, ignoring binding); the **structure gap** between them is how much apparent capture fails a binding check.

| Rank | Vendor | **Fair total** (structure-aware) | Content recall | Structure gap | Unsupported | Cost (599pp) | Coordinates |
|---:|---|---:|---:|---:|---:|---:|:--:|
| 1 | **Gemini 3.5 Flash** | **89%** | 92% | −3 | 8% | $7.12 | coarse |
| 2 | **Landing AI** (DPT-2) | **86%** | 89% | −3 | 11% | paid | **exact boxes** |
| 2 | Gemini 3.1 Flash-Lite | **86%** | 90% | −4 | 8% | **$1.12** | coarse |
| 2 | **LlamaParse** (agentic) | **86%** | 90% | −4 | 10% | paid (agentic tier) | **exact boxes** |
| 2 | **Pulse** (Ultra 2, advanced) | **86%** | 90% | −4 | **5%** | ~10 cr/pg | **exact boxes** |
| 6 | **Mistral OCR 4** (advanced) | **80%** | 84% | −4 | **19%** | ~$3 ($5/1k) | **exact boxes** |
| 7 | PyMuPDF | **68%** | 84% | **−16** | 5% | **$0** usage¹ | exact boxes |
| 8 | LiteParse | **62%** | 80% | **−18** | 8% | $0 (local) | exact boxes |
| 9 | Tesseract | **52%** | 64% | **−12** | 15% | $0 | word boxes |
| ◆ | gpt-5 (image) | 88% ◆ | 91% | −3 | 9% | $13.82 | coarse |
| ◆ | gpt-5 (file) | 87% ◆ | 91% | −4 | 9% | $12.54 | coarse |

> **Scores are structure-aware** (binding-aware rubric, both judge families). Landing AI is the current DPT-2 model; all eleven vendors were judged with byte-identical prompts and shuffles. Four additions were validated as controlled changes — the DPT-2 re-judge as a swap (every other vendor's aggregate moved <1.1pp; [`LANDINGAI_DPT2_REBENCH.md`](LANDINGAI_DPT2_REBENCH.md)), **LiteParse as an add** (re-judged 9-up; the existing eight moved <1.34pp; [`LITEPARSE_ADD.md`](LITEPARSE_ADD.md)), **Mistral OCR 4 as an add** (re-judged 10-up with weights frozen to canonical; the existing nine moved <1.41pp across all four judge passes; [`MISTRAL_ADD.md`](MISTRAL_ADD.md)) and **Pulse as an add** (re-judged 11-up; the existing ten moved <1.04–1.37pp on three of four passes, and a benign uniform +0.87pp leniency drift of 1.91pp on the gpt-5-structure pass — same sign on all ten, no headline ranking change — was audited and force-spliced; [`PULSE_ADD.md`](PULSE_ADD.md)). The structure change is identical across judges (PyMuPDF −16 under *both* gpt-5 and Gemini). Ranking order: Gemini Flash clear #1, at the top of a **five-way 86–89 high-quality cluster** (with Landing AI, Flash-Lite, LlamaParse and **Pulse** at 86 — the last the cleanest, 5% unsupported); **Mistral OCR 4 a vision-tier standalone at 80% — but with the highest unsupported rate of any vendor (19%), because its advanced figure-annotation layer fabricates on graphics it can't read (see [`MISTRAL_ADD.md`](MISTRAL_ADD.md))**; the three local text-layer tools fall to a separate class. The content-recall numbers (graded against the corrected v2 `GROUND_TRUTH.md`; see §9) are preserved in `results/_fair_total_judging_content.json`.
>
> *Earlier measurement fixes that still hold:* the **judge-input truncation** fix (6,000→16,000-char cap, deflated only Landing AI; [`AUDIT_VEND_CAP.md`](AUDIT_VEND_CAP.md)) and the **LlamaParse tier** fix (`accurate`→`agentic`, +18–22 pp; [`AUDIT_LLAMAPARSE_MODE.md`](AUDIT_LLAMAPARSE_MODE.md)).

**How to read the columns together:** `fair total` is *structure-aware completeness*; `content recall` is *presence ignoring binding*; their gap is *structure preservation*; `unsupported` is *fidelity* (now counting an actively wrong binding as a contradiction).
- **Gemini 3.5 Flash (89% / gap −3 / 8%)** — the best *balance*: top structure-aware capture, smallest gap, low padding.
- **Landing AI (86% / gap −3 / 11%)** — on DPT-2 it is a genuine structure-preserver (gap tied with the best) and the only top-tier vendor with exact element coordinates; its remaining cost is mid-pack padding and a relative softness on the densest charts.
- **PyMuPDF (68% / gap −16 / 5%)** — the gap is the headline: it recovers characters but loses the structure they depend on. Its `unsupported` is low only because a flat dump *strands* values away from their keys rather than inventing them.

**By genre** (full table in [`results/BY_DOCUMENT.md`](results/BY_DOCUMENT.md), gpt-5 judge): the annual report is the easy genre (real vendors converge — Gemini Flash 94, LlamaParse 94, Landing AI 93) and the chart-heavy M&A memo is the great separator (Gemini Flash 85 → Landing AI/Flash-Lite 78 → LlamaParse 76 → PyMuPDF 59 → Tesseract 38). DPT-2's gains for Landing AI are concentrated exactly there: SOTER (M&A memo) 71→78 and Alpha (French consulting) 73→81, while the already-saturated annual report moved least (91→93).

---

## 3. Where each vendor wins and loses — structure-aware fair total by category

| Vendor | Text (149) | Table (128) | Chart (152) | Mixed (113) | Cover (55) | Image (2) |
|---|---:|---:|---:|---:|---:|---:|
| **Gemini 3.5 Flash** | 95% | **87%** | **84%** | **93%** | 84% | 82% |
| **Landing AI** (DPT-2) | 95% | 86% | 78% | 90% | 82% | **88%** |
| Gemini 3.1 Flash-Lite | 94% | 85% | 78% | 89% | **85%** | 68% |
| **LlamaParse** (agentic) | **96%** | 85% | 76% | 92% | 77% | 42% |
| **Pulse** (Ultra 2, advanced) | **97%** | **90%** | 73% | **93%** | 61% | 84% |
| **Mistral OCR 4** (advanced) | **96%** | 85% | 62% | 87% | 61% | 86% |
| PyMuPDF | 80% | 71% | 54% | 79% | 51% | 28% |
| LiteParse | 85% | 60% | 44% | 71% | 50% | 54% |
| Tesseract | 78% | 50% | 33% | 59% | 31% | 37% |
| gpt-5 (image) ◆ | 96% | 85% | 82% | 92% | 92% | 90% |
| gpt-5 (file) ◆ | 94% | 83% | 82% | 92% | 89% | 79% |

> Counts are pages per category. **Image/Photo is only 2 pages** (the corpus treats photo-filled title pages as Cover/Divider by function) — read that column as anecdote, not signal. Numbers are structure-aware (bindings required).

**The story the columns tell (now that binding is scored):**
- **Chart** is the great separator. The vision LLMs (82–84%), **Landing AI 78%** and **LlamaParse agentic 76%** read and *correctly bind* label-free bars/lines; **Pulse (73%)** and **Mistral (62%)** sit between that tier and the collapse below it; the pure text-layer tools fall apart once geometry/series binding is required — PyMuPDF **54%** (was 79% on content alone), Tesseract 33%. DPT-2 lifted Landing AI's chart score (73→78), putting it just ahead of LlamaParse and second among real vendors after the Gemini/gpt-5 vision tier.
- **Table** spreads more than it did on content recall: **Pulse 90%** leads, then Gemini 87%, **Landing AI 86%**, LlamaParse/Flash-Lite/Mistral 85%, **PyMuPDF 71%** (its side-by-side-table interleaving costs it the binding check), Tesseract 50%. DPT-2 moved Landing AI to within a point of the vision-LLM table lead (80→86).
- **Text** is still solved by everyone with vision or a text layer (94–97%, Pulse on top); PyMuPDF (80%) and Tesseract (78%) trail because some "text" pages carry callouts/columns whose order they scramble.
- **Cover/Divider** is where structure barely matters (sparse pages), so PyMuPDF (51%) is unchanged from content — its cover weakness is *visual*, not structural. The vision models handle them (80–92%).

---

## 4. The per-capability matrix (diagnostic view)

The fair total answers "how much of the document," but for *engineering decisions* you often need the per-capability picture. From `results/EXTRACTION_COMPARISON.md` (Gen-2 element-level metrics):

| Vendor | Content recall | Numbers (finance) | Table recovery | Graph data | Diagram struct | Reading order | Coords | Cost |
|---|---:|---:|---:|---:|---:|---:|:--:|---:|
| gpt-5 (image) | 97% | 96% | 90% | 85% | 66% | 67% | coarse | $13.82 |
| gpt-5 (file) | 97% | 97% | 91% | 84% | 70% | 60% | coarse | $12.54 |
| **Gemini 3.5 Flash** | 97% | 96% | **98%** | **85%** | **91%** | 67% | coarse | $7.12 |
| Gemini 3.1 Flash-Lite | 96% | 95% | 94% | 83% | 82% | 67% | coarse | **$1.12** |
| Landing AI ⁂ | 95% | 93% | 91% | 80% | 82% | 63% | **exact** | paid |
| **LlamaParse** (agentic) | 97% | 95% | 99% | 77% | 83‡ | – | **exact** | paid |
| **Mistral OCR 4** (advanced) | 96% | 94% | 94% | 59% | 60% | – | **exact** | ~$3 ($5/1k) |
| **Pulse** (Ultra 2, advanced) | 97% | 96% | 94% | –§ | –§ | – | **exact** | ~10 cr/pg |
| PyMuPDF | 97% | 97% | 57% | 29% | 29% | **90%** | **exact** | $0 |
| LiteParse | 96% | 95% | 81% | 12% | 14% | – | **exact** | $0 |
| Tesseract | 88% | 72% | 0% | 24% | 29% | 68% | word | $0 |

> **⁂ The Landing AI row is the legacy endpoint.** This element-level diagnostic has **not yet been re-run on DPT-2** (unlike the headline fair total in §2–§3, which is DPT-2). Read it as a **floor**: DPT-2 raised Landing AI's structure-aware table score 80→86 and chart 73→78 (§3), so its table-recovery / graph-data here would likely rise on a re-run. Flagged for follow-up.

Two reading notes carried from the methodology:
- **‡ LlamaParse diagram structure** is shown as the **element-level** judge's score (83), not the figure judge's (30). The figure judge reads only *figure-typed* blocks, but LlamaParse-agentic delivers diagram content as **inline markdown prose** — so the figure judge under-counts it while the element-level judge (reading its full markdown) credits it. Its graph-data 77 (up from 44 at the accurate tier) is the figure judge's. See the caveat in [`results/EXTRACTION_COMPARISON.md`](results/EXTRACTION_COMPARISON.md).
- **§ Pulse graph-data / diagram-structure shown as `–`.** Pulse was added to the headline fair total only, not the structured figure judge: in its advanced config its `Images[]` are bare `[Image]` placeholders and it weaves chart/diagram understanding **inline into the page markdown**, so running the structured judge on it would manufacture a misleading ≈0. Its figure reading *is* measured — by its **Chart-category fair total = 73%** (§3, above Mistral's 62), which reads that full markdown. See [`PULSE_ADD.md`](PULSE_ADD.md).
- **Reading order** is Kendall-τ vs a text-layer reference; **PyMuPDF's 90% is inflated** because the reference uses the same layout engine. Treat it as a capability flag (parsers emit exact element order), not a ranking.
- **Content/numeric recall saturate** at 95–97% — they cannot discriminate the serious vendors, which is *why* the structure-aware fair total exists. These per-capability dimensions (**table recovery, graph data, diagram structure**) already price structure, and they corroborate the headline change exactly: the tools that crater on them (PyMuPDF graph-data 29, diagram-struct 29, table-recovery 57; LiteParse graph-data 12, diagram 14; Tesseract worse) are precisely the three local text-layer tools that lose 11–18 pts when the fair total goes structure-aware. The structure-aware fair total spread among real vendors is now ~37 pp (Tesseract 52 → Gemini Flash 89) vs ~2 pp for token recall.

> **Gemini 3.5 Flash is the standout on the figure dimensions** — top-tier graph-data fidelity (85%, level with gpt-5's 84–85%) and a commanding diagram-structure lead (**91%** vs gpt-5 66–70%, Landing AI 82% legacy) — at half gpt-5's cost. This is the single biggest capability finding in the matrix.

---

## 5. The table-recovery correction (the question that started this)

This deep-dive began with a correct instinct about the **legacy** Landing AI run: *"Landing AI's table extraction at 60% — I don't buy it."* It was right.

| | Landing AI table score (legacy endpoint) |
|---|---:|
| Original metric (`table_presence_legacy`) | **56%** ❌ |
| Corrected metric (`table_recovery`) | **91%** ✅ |

**The 56% was a metric artifact, not a Landing AI weakness and not a ground-truth error.** Two bugs:

1. **Collector dropped figure-embedded tables.** Landing AI's ADE classifies a table that contains a logo/photo/icon as a `figure` chunk — whose text nonetheless holds the *full table*. The collector only counted literal `table` chunks, silently discarding those tables. *Fixed:* detect figure-embedded tables structurally (requires the word "table" **and** bullets/pipes/digits). The DPT-2 collector (`collect_landingai_dpt2`) carries the same fix.
2. **Denominator demanded a table where none existed.** The metric required a table on every `Table`∪`Mixed` page, but ~half of `Mixed` pages are chart+text with no table. That punished Landing AI's *correct abstention* and rewarded over-emission (the accurate-tier LlamaParse emitted a table on every no-table Mixed page checked; agentic LlamaParse instead tabulates real chart data). *Fixed:* score only the 128 true `Table` pages.

A tree-wide audit of the other collectors confirmed **no analogous bug**. This correction is *why* Landing AI was never trapped in a false "60% tier" — and on the current DPT-2 model its structure-aware **table** score is **86%** (§3), confirming the table strength the corrected metric first revealed. *(The 56→91 numbers above are the legacy-endpoint element metric; the 86% is the DPT-2 structure-aware fair total.)*

---

## 6. Cost and speed — the operational axes

| Vendor | Cost / 599pp | Speed (s/page) | Fair total (structure-aware) | $ per point of capture |
|---|---:|---:|---:|---:|
| PyMuPDF | $0 usage¹ | **0.11** | 68% | $0¹ |
| Gemini 3.1 Flash-Lite | $1.12 | 4.4 | 86% | ~$0.013 |
| Mistral OCR 4 (advanced) | ~$3 ($5/1k) | 5.2 | 80% | ~$0.038 |
| Pulse (Ultra 2, advanced) | ~10 cr/page | 18.8 ◇ | 86% | — |
| Gemini 3.5 Flash | $7.12 | 6.9 | 89% | ~$0.080 |
| gpt-5 (file) ◆ | $12.54 | 26.9 | 87% ◆ | ~$0.144 |
| gpt-5 (image) ◆ | $13.82 | 27.1 | 88% ◆ | ~$0.157 |
| LlamaParse (agentic) | paid (agentic tier) | 1.3 ‡ | 86% | — |
| LiteParse | $0 (local) | 1.3 | 62% | $0 |
| Tesseract | $0 | 1.2 | 52% | $0 |
| Landing AI (DPT-2) | paid (3 credits/page) | 21.5 † | 86% | — |

**The cost curve is brutally clear:** spending more than Gemini Flash-Lite buys *diminishing returns*. Flash-Lite captures **86%** (structure-aware) for **$1.12**; gpt-5 reaches only **87–88%** (and only as an upper-bound ◆) for **11–12× the price**. Gemini 3.5 Flash is the sensible top — **89% at $7.12, half of gpt-5, and it edges gpt-5's own upper-bound rows** while leading on diagram structure. There is no quality argument for gpt-5 on this corpus that survives the price tag. The two paid parsers (Landing AI, LlamaParse) earn their fee on a *different* axis — exact coordinates — not on raw capture, where the cheap Gemini tier matches them. Note that PyMuPDF's "free" value proposition weakens once structure is scored (68%, not 84%) — it is free for *text + simple tables*, not for figures or complex layouts.

**Speed reads the opposite way from quality.** The fastest tool is the cheapest-and-weakest class (PyMuPDF, **0.11 s/page**, local) and the slow end is the reference-grade and document-AI tier (gpt-5 **~27 s/page** full-markdown extraction; Landing AI **21.5 s/page** on DPT-2, median 17.1) — so on this corpus latency does *not* buy capture. The Gemini vision models cluster at **4–7 s/page**, the cheaper Flash-Lite (4.4 s) *faster* than its bigger sibling (6.9 s) — the quickest LLM in the field. *(An earlier revision quoted gpt-5 at 4.1/7.0 s/page — those were its page-**classification** pass, a lighter task than the scored extraction; the ~27 s figures are the like-for-like extraction latency.)* Three measurement caveats matter before trusting these:
- **Per-page mean, not whole-corpus runtime.** Every cloud vendor ran under 4–8 concurrent workers, so wall-clock for the full corpus ≈ (s/page × 599) ÷ workers. Only the **per-page mean** is a clean cross-vendor comparison; the implied totals are not.
- **† Landing AI is penalized by the harness.** It is natively a whole-document service (and its async Parse Jobs API handles up to 1,000-page files) but was driven **page-by-page** here (render → one POST per page), so 21.5 s/page eats per-page network + retry overhead on every call and **overstates its production latency** — run whole-doc it is materially faster.
- **‡ LlamaParse's figure is derived, not measured.** Its API is a whole-document async job; 1.3 s/page is the doc-level wall time amortized over pages (`_wall_s ÷ page_count`), not a per-page latency comparable to the others' per-call measurements.
- **◇ Pulse's 18.8 s/page is genuine, not a harness artifact** — it is the real per-page latency of the `refine` re-OCR pass (median 18.8, mean 19.6, p90 28). Unlike Landing AI's harness penalty, this is the cost of Pulse's most-advanced tier; run 6-way parallel here, full-corpus wall was ~33 min (~3.3 s/page effective throughput). The latency *is* the fidelity trade.

Local tools (PyMuPDF, Tesseract) have no network in the loop; the cloud numbers include network, queueing, and retry backoff. Source: per-page `seconds` recorded for all 599 pages in each vendor's extraction-run JSON — `results/_openai_*_extract.json` and `results/_gemini_*_extract.json` for the LLMs, `results/_*_solution.json` for the local tools, and the raw run directories for Landing AI DPT-2 / Mistral / Pulse. (The speed table in `results/COMPARISON.md` is the earlier classification-era run and predates the DPT-2/Mistral/Pulse additions.)

> ¹ **PyMuPDF is not free for enterprise/proprietary use.** The $0 above is the *usage* cost (no API fee); the **license** is dual **AGPL-3.0 or a paid Artifex commercial license**. AGPL's network-copyleft (§13) means a proprietary or SaaS product must release its *entire* source under AGPL or buy a commercial license — so PyMuPDF's true cost in a typical enterprise is a license negotiation, not $0. Genuinely permissive text-layer alternatives: **pdfplumber (MIT)**, **pypdf (BSD)**. **Tesseract is Apache-2.0** — its $0 *is* license-free. Treat "free text-layer parser" in this report as "PyMuPDF *or a permissive equivalent*"; the structure-aware capture numbers (68% etc.) are properties of the text-layer-extraction *class* and carry over to pdfplumber/pypdf, which are the deploy-anywhere choices.

---

## 7. Per-vendor profiles

**Gemini 3.5 Flash — the recommended default.** Top structure-aware capture (89%, smallest gap −3), best-in-class diagrams (91% diagram-structure) and top-tier charts (85% graph-data), excellent image description, low padding (8%), $7.12. Weakness: coarse coordinates only (no element boxes), and one runaway-repetition empty page in 599 (a minor robustness ding). *Use it for almost everything.*

**Gemini 3.1 Flash-Lite — the value champion.** 86% (structure-aware) for $1.12 — within ~3 points of its big sibling at a sixth of the cost. Slightly weaker on charts. *Use it at scale, or as the figure-extraction half of a hybrid (§8).*

**Landing AI — the coordinates-grade specialist, now a top-tier capturer (DPT-2).** On its current `dpt-2-latest` model: **86% structure-aware** (gap −3, a genuine structure-preserver), strong tables (86%), reads charts (78%), **best-in-class Image/Photo (88%)**, and — uniquely among the high-quality tier (with LlamaParse) — **exact element bounding boxes**. DPT-2 was a real upgrade over the legacy endpoint (corpus 81→86 gpt-5 / 92→94 Gemini, both families agreeing; padding 17→11%; biggest gains on the chart-heavy and consulting-deck genres) — full trail in [`LANDINGAI_DPT2_REBENCH.md`](LANDINGAI_DPT2_REBENCH.md). Residual relative weakness on the densest charts (78%, still 2nd among real vendors). *Use it when you need precise layout grounding / element coordinates, enterprise document workflows, or auditable region-level provenance — things no LLM gives you — now without giving up top-tier capture.*

**PyMuPDF — the cheap text/table first pass (not a top-tier extractor; AGPL-licensed).** **68% structure-aware** (84% content recall — a **−16 structure gap**, the largest of any vendor) for $0 *usage*. Perfect text and decent simple tables, but it recovers characters while losing the structure they depend on: it **merges side-by-side tables and destroys relational-diagram bindings** (org charts, process flows), and is blind to chart geometry (29% diagram structure). The structure-aware re-judge under *both* judge families drops it identically (84→68). Collapses entirely on scanned documents. **License caveat:** PyMuPDF is **AGPL-3.0 or a paid Artifex commercial license** — *not* free for proprietary/SaaS deployment (see cost-table note ¹). For born-digital text extraction with a permissive license, **pdfplumber (MIT) / pypdf (BSD)** occupy the same tier without the copyleft. See [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md), [`AUDIT_PYMUPDF_STRUCTURE.md`](AUDIT_PYMUPDF_STRUCTURE.md). *Use a text-layer parser as a near-free first pass for born-digital text + simple tables, then escalate figures/diagrams/complex tables to an LLM.*

**LlamaParse (agentic) — the coordinates-grade all-rounder.** In its most capable `agentic` tier (an LVM agent loop), 86% structure-aware (gap −4, holds up), perfect text (96%), strong tables, and — unlike the pure text-layer parsers — it **reads figures** with bindings intact: charts 76% and diagrams 83% (element-level), plus **exact element bounding boxes**. *Use it when you want both figure comprehension and coordinate-level provenance in one paid parser.* **Critical:** this requires the **`agentic` tier** — the middle `accurate` tier silently drops whole born-digital pages and scores only 71% (see [`AUDIT_LLAMAPARSE_MODE.md`](AUDIT_LLAMAPARSE_MODE.md)). Choosing the tier is the single biggest LlamaParse decision.

**LiteParse — fast local text-and-prose pass, *below* PyMuPDF on structured data (run-llama OSS, Apache-2.0).** **62% structure-aware** (80% content recall — a **−18 structure gap, the largest of any vendor**) for $0, fully local, ~1.3 s/page. It is the open-sourced core of LlamaParse *minus* the VLM layer (PDFium native text → an anchor "grid-projection" → heuristic markdown; Tesseract OCR auto-triggers only on sparse pages — which on this born-digital corpus was ~1/599). Being **vision-blind** it is the **worst figure reader of all ten** (graph-data 12%, diagram-structure 14% — below even PyMuPDF's flat dump, because its reconstruction *scatters* the raw chart numbers a dump preserves verbatim). The twist vs PyMuPDF: its grid markdown emits far more table/heading *shape* (table-presence 81% vs 57%) and it **beats PyMuPDF on plain text (85 vs 80) and image/photo (54 vs 28)**, but it **loses on every structured category** (Table 60 vs 71, Chart 45 vs 54, Mixed 71 vs 79) because on dense multi-column finance pages the projection merges adjacent columns into a jumble whose row/column bindings are unrecoverable — so the table-shaped output earns no structure credit. It *does* emit exact element bounding boxes. *Use it as a fast, deploy-anywhere, permissively-licensed first pass for born-digital text + prose; for finance tables/charts PyMuPDF+fitz's native table finder is the stronger free baseline and any vision tool is a tier above.* Full add-trail: [`LITEPARSE_ADD.md`](LITEPARSE_ADD.md).

**Tesseract — scanned-document last resort.** 52% structure-aware (gap −12), 0% structured tables, 72% numeric recall (OCR drops digits), and the **highest padding of any local tool (15%; only Mistral's 19% is higher overall)**. *Use it only when there is no text layer and no budget for a vision model.*

**gpt-5 (image/file) ◆ — reference-grade, not cost-justified here.** 87–88% (upper bound, gap −3/−4), but $12–14 and *behind Gemini on diagram structure and edged by Gemini Flash on the structure-aware total*. *Worth it only if you specifically need the OpenAI ecosystem; otherwise Gemini Flash dominates on price and figures.*

---

## 8. Recommendations by use case

| If you need… | Use | Why |
|---|---|---|
| **Best overall extraction, sane budget** | **Gemini 3.5 Flash** | 89% structure-aware capture, best figures, $7.12, low padding |
| **Extraction at massive scale / lowest cost with quality** | **Gemini 3.1 Flash-Lite** | 86% for $1.12 — the value frontier |
| **Exact element coordinates / layout provenance** | **Landing AI (DPT-2)**, **LlamaParse (agentic)** or **Pulse (Ultra 2)** | the three coordinate-grade members of the 86–89 tier, all with exact boxes; LlamaParse reads figures inline, Landing AI emits a single whole-doc ADE pass (the 21.5 s/page in §6 is the page-by-page harness, not its native latency †), Pulse adds the lowest fabrication of the field (5%) at the cost of `refine` latency (◇) |
| **Figure comprehension + coordinates in one paid parser** | **LlamaParse (agentic)**, **Landing AI (DPT-2)** or **Pulse (Ultra 2)** | all 86% structure-aware with exact boxes; LlamaParse delivers diagrams as inline markdown, Landing AI leads on image/photo, Pulse leads on text/tables and fidelity — pick on coordinate-format, latency tolerance, and whole-doc vs page workflow |
| **Lowest-fabrication output for audit-sensitive ingestion** | **Pulse (Ultra 2)** | 86% capture with **5% unsupported — the lowest of any vision vendor** (Mistral, same capture class on text/tables, runs 19%); the trade is ~19 s/page `refine` latency |
| **Near-free text + *simple* tables on born-digital PDFs** | **A text-layer parser** (pdfplumber/pypdf if you need a permissive license; PyMuPDF only if AGPL-compliant or licensed), escalate figures/diagrams/complex tables to an LLM | $0 usage, perfect text layer — but loses structure on charts, relational diagrams, and side-by-side tables; mind PyMuPDF's AGPL license (note ¹) |
| **Maximum fidelity, cost no object, OpenAI stack** | gpt-5 (file) | reference-grade (but Gemini matches it cheaper) |
| **Scanned documents, no text layer** | a vision LLM (Gemini) or Landing AI; Tesseract only as floor | text-only tools collapse without a text layer |

**The hybrid worth building:** **a text-layer parser for text + simple tables, Gemini 3.1 Flash-Lite ($1.12) for the figure/diagram/complex-layout pages.** (Use **pdfplumber/pypdf** for the text-layer half if you need a permissively-licensed, deploy-anywhere stack; PyMuPDF is faster but AGPL — note ¹.) The text layer is unbeatable value where structure is simple; routing the chart/diagram/multi-table/image pages to a cheap vision model patches its structure blind spot — plausibly approaching top-tier capture for a few dollars per document. The structure-aware numbers make the routing boundary sharper: send anything with bindings (charts, org charts, side-by-side tables) to the LLM. If the workload *also* needs auditable element coordinates, swap the LLM half for **Landing AI (DPT-2) or LlamaParse-agentic** — same capture tier, plus exact boxes.

> **The born-digital caveat that changes everything for scanned docs:** all three test PDFs have a clean text layer, which is *why* PyMuPDF reaches even 68% at $0 usage (license caveat ¹) and content recall saturates. **On scanned or photographed documents the text-layer floor disappears** — PyMuPDF would crater, Tesseract's OCR errors would dominate, and the gap between the vision LLMs / Landing AI and everything else would widen sharply. Choose accordingly: the rankings above are for born-digital documents.

---

## 9. Ground-truth validation — what we stress-tested and what we changed

The benchmark's foundation is `GROUND_TRUTH.md`, a 599-page transcription **built by gpt-5** and judged by a **gpt-5** judge. That twin co-location is the one place a shared blind spot could corrupt every number, so we attacked it on three independent axes. Full detail: [`GT_VALIDATION.md`](GT_VALIDATION.md). **We did not just confirm the reference — we found real defects, corrected them, and re-measured.**

**1. Independent faithfulness audit (Claude, a different model family).** A **36-page chart-weighted** sample (3.4× the original check), every flagged page re-verified by hand at high zoom. Result: **30 faithful, 2 minor, 4 *material* defects — all four on dense multi-series figures** (e.g. SOTER p30, where gpt-5 replaced 17 of 21 *printed* ARPU labels with a smoother invented series; p102, a subscriber chart whose (2.2) churn bar was omitted). An earlier "16/16 faithful" spot-check had simply not sampled the hard figure pages. Text, prose, and financial tables remained faithful — including arithmetic-checkable statements (IAR p258/p265 foot internally and tie cross-page: profit-before-tax **48,937** appears identically on both).

**2. The root cause, and the fix.** All three PDFs are born-digital, so every printed number lives in the **text layer** — an exact, vision-free oracle. A text-layer diff over all 599 pages put v1 printed-number fidelity at **97.5% on charts / 98.4% overall** (the GT was far better than the worst pages implied), but the figure errors were real and, crucially, **biased the benchmark *against* the text-layer parsers**: a vendor that correctly read `185, 184, 201` was scored as *disagreeing* with gpt-5's hallucinated `165, 166, 135`. We rebuilt all 275 figure pages with the **authoritative text layer + a 2400px render** (`build_gt_md_v2.py`), raising printed-number fidelity to **99.1% charts / 99.5% overall** and fixing every audited defect. This corrected `GROUND_TRUTH.md` is now canonical (v1 archived as `GROUND_TRUTH_v1.md`).

**3. Re-measure — does the correction move the ranking?** Same vendors, same judge, only the corrected reference. **The ranking is identical.** But the fix removed exactly the twin bias: on chart pages the text-layer vendors gained most (**PyMuPDF +7.6, LlamaParse +6.4, gpt-5-file +4.4**) while **gpt-5-image — the one model sharing the GT's blind spot — was the only vendor that did not improve (−0.2)**. That file-gains/image-flat split is direct evidence the effect was real and is now corrected.

**4. Cross-family judge.** Re-judging the corrected GT with a non-OpenAI judge (**Gemini 3.5 Flash**, byte-identical prompt/shuffle) keeps the **same top set with Gemini Flash #1 under both judges**. Both judges also agree on the two later vendor-version changes — the agentic-tier LlamaParse re-run and the **DPT-2 Landing AI re-benchmark** (Landing AI rises under both families; [`LANDINGAI_DPT2_REBENCH.md`](LANDINGAI_DPT2_REBENCH.md)). Neither judge favours its own family (the Gemini judge scores gpt-5-image level with its own Gemini Flash). See [`results/FAIR_TOTAL_JUDGES.md`](results/FAIR_TOTAL_JUDGES.md).

> **Note — §9 is about GT *content* fidelity, and predates the later vendor-version changes.** It validates that the ground-truth transcription has the right *numbers* (a text-layer-anchored correctness check), which is orthogonal to — and still holds under — the structure-aware metric and the DPT-2/agentic re-runs (all re-judge vendors against the *same* corrected GT). The re-measure deltas quoted here (e.g. PyMuPDF +7.6 on charts) are **content-recall-era** numbers run with the original **accurate-tier** LlamaParse and **legacy** Landing AI. The agentic-tier and structure-aware changes ([`AUDIT_LLAMAPARSE_MODE.md`](AUDIT_LLAMAPARSE_MODE.md), [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md)) and the DPT-2 Landing AI re-benchmark all reproduce under both judge families.

**Conclusion:** the v1 reference was sound on the born-digital majority but had a real, *correctable* error rate on dense figures that mildly **flattered the image-mode LLMs**. Corrected and re-measured, the **ranking holds and the numbers are more accurate**. *(Layer 1, the category key, was separately audited via gpt-5 third-vote triangulation — `results/GROUND_TRUTH_AUDIT.md` — and found sound.)*

---

## 10. Caveats

1. **Born-digital corpus.** All three PDFs have clean text layers; rankings would shift on scanned documents (§8).
2. **gpt-5 is transcriber and judge.** The reference was independently audited (Claude), found to have material defects **only on dense figures**, **corrected** via a text-layer-anchored rebuild, and the ranking confirmed stable under both the corrected GT and a non-OpenAI (Gemini) judge (§9). gpt-5's own rows are flagged ◆ and excluded from the ranking.
3. **Chart data is inherently estimated** for label-free figures; those scores carry more uncertainty than table scores (printed labels are now anchored to the text layer; only genuinely unlabeled geometry remains estimated).
4. **Single judge pass**, not a panel — stabilized by blind shuffling and the contradiction-only fidelity definition. Per-page judge scores carry real variance (±20–25 pp page-to-page, measured by replicate runs), which is why all conclusions are read off the **weighted corpus aggregate** (stable to ~±1.5 pp) and cross-checked across two judge families, never off single pages.
5. **n = 3 documents** (599 pages) — trust the wide gaps most, the within-few-points gaps least. In particular the 86% four-way cluster (Landing AI / Flash-Lite / LlamaParse / Pulse) is a statistical tie; do not over-rank within it.
6. **Costs are point-in-time** on this corpus. Landing AI's dollar figure was not captured — DPT-2 bills **3 credits/page** (≈1,797 credits for the corpus), but the per-credit price was not recorded, so it is shown as `paid`. Pulse likewise bills in credits (**10/page**, ≈5,990 for the corpus) with the per-credit price not recorded.
7. **Judge-input length (audited & fixed).** Vendor text and the GT reference are fed to the judges at no-truncation caps on this corpus. An earlier 6,000-char/page cap deflated only Landing AI (longest output) in the fair-total and element evals; the figure judge had per-figure/blob caps (1,600/7,000) that mildly clipped Landing AI and gpt-5. Both were corrected pre-publication and re-judged — fair-total/element moved Landing AI +2–13pt, the figure dimensions ±≤3pt — **no ranking changed in any eval**. Full trail: `AUDIT_VEND_CAP.md`.
8. **Vendor tier/mode/model is a first-class variable (audited & fixed — twice).** (a) LlamaParse was originally run in its middle `accurate` tier, which silently dropped whole born-digital pages; re-running at its most capable `agentic` tier lifted it +18.5/+21.8 pp (both judge families) and changed its rank (8th→3rd among real vendors). Full trail: `AUDIT_LLAMAPARSE_MODE.md`. (b) **Landing AI was originally run on its legacy pre-DPT-2 endpoint**; re-benchmarking on the current `dpt-2-latest` model (full 599 pages, both families, validated controlled swap) lifted it 81→86 (gpt-5) and 92→94 (Gemini), moving it from 4th into the 86 tier, and cut its padding 17→11%. Full trail: [`LANDINGAI_DPT2_REBENCH.md`](LANDINGAI_DPT2_REBENCH.md). **Lesson: benchmark every vendor's most capable current mode.**
9. **Element-level / figure diagnostics lag the headline.** The headline fair total (§2–§3, §6) is DPT-2 for Landing AI, but the per-capability matrix (§4) and the table-recovery correction (§5) are from the legacy-endpoint element eval and are flagged ⁂ where they appear; they are a lower bound for DPT-2. The separate 6,129-element decomposition eval (`results/WHO_IS_GOOD_AT_WHAT.md`) was likewise never run for the three later additions (LiteParse, Mistral, Pulse) — their §4 cells come from the objective + figure evals, which did include them. Re-running the element tier across the current field is the open follow-up.
10. **Structure is now scored, not caveated (resolved 2026-06-14).** The earlier content-recall rubric credited *information present* regardless of whether its binding survived, which inflated the pure-text-dump tools. The headline fair total is now **structure-aware** — a value counts only if its row/column/series/node binding is recoverable, and an actively wrong binding counts as a contradiction. Re-judged across all 599 pages under **both** judge families: PyMuPDF 84→**68**, Tesseract 64→**52**, every structure-preserving vendor ≤6 pp; the change is identical across families. Content recall is retained as a labeled diagnostic and the **structure gap** is reported per vendor (§2). Full methodology: [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md); origin audit: `AUDIT_PYMUPDF_STRUCTURE.md`.
11. **Speed is per-call latency under concurrency — recorded, not headline (§6).** Per-page extraction `seconds` is logged for all 599 pages, but it is per-call wall time measured with 4–8 concurrent workers, so it is **not** whole-corpus runtime. Two vendors' figures are not directly comparable to the others': **Landing AI** was driven page-by-page (overstating its native whole-doc latency, †) and **LlamaParse**'s per-page number is doc-level async time amortized over pages (‡). Local tools (PyMuPDF/Tesseract) exclude network. Treat the per-page mean as the comparable signal and the wide gaps (≈245× from local to gpt-5's full extraction) as the takeaway; speed is an operational axis, deliberately kept out of the capture-quality headline.

---

## 11. Appendix — corpus & artifacts

**Corpus:** `20190308_Projet_Alpha_Restitution` (156pp, French consulting deck) · `IAR_FY25_EN` (310pp, English annual report) · `SOTER - Company Presentation - vFF` (133pp, English investor deck). 599 pages total.

**Ground-truth build:** `GROUND_TRUTH.md` (v1) — gpt-5 vision, 1,502,226 chars, **$22.18**, 0 empty pages. **Correction (v2, now canonical):** 275 figure pages rebuilt with the authoritative text layer + 2400px render, **$11.77**; printed-number fidelity 98.4%→99.5% (§9). Fair-total judge — gpt-5, **$12.67/run**; cross-family Gemini judge **$7.05**. **DPT-2 Landing AI re-benchmark (2026-06-15):** parse ≈1,797 credits; re-judging $31.65 (gpt-5 structure $12.05 + Gemini structure $7.27 + gpt-5 content $12.33).

**Key artifacts:**
- [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md) — **the canonical metric definition**: why and how scores are structure-aware (bindings required), content-vs-structure under both judge families, per-category validation
- [`LANDINGAI_DPT2_REBENCH.md`](LANDINGAI_DPT2_REBENCH.md) — **the DPT-2 re-benchmark**: legacy→DPT-2 endpoint, PNG-vs-PDF input A/B, validated controlled-swap splice, full before/after (both judge families)
- `results/FAIR_TOTAL.md` — headline metric (structure-aware; content recall + structure gap columns)
- `GT_VALIDATION.md` — the three-axis ground-truth validation (audit → correction → re-measure → cross-family judge)
- `AUDIT_VEND_CAP.md` — the judge-harness audit: the VEND_CAP truncation artifact found, fixed, and re-measured under both judge families
- `AUDIT_LLAMAPARSE_MODE.md` — the LlamaParse tier audit: `accurate` vs the canonical `agentic` tier (+18.5/+21.8 pp), both judge families
- `results/BY_DOCUMENT.md` — results sliced by document **genre** (annual report / M&A info memo / French consulting report): fair-total by doc and by category×doc, both judge families
- `AUDIT_PYMUPDF_STRUCTURE.md` — the PyMuPDF structure audit: content recall over-credits structure loss for pure-text-dump tools
- `results/vendor_md/README.md` — per-vendor ground-data manifest (11 byte-faithful single-md extractions, 599 pages each; LlamaParse = agentic, Landing AI = DPT-2)
- `results/FAIR_TOTAL_V1_V2.md` — pre/post-correction deltas · `results/FAIR_TOTAL_JUDGES.md` — gpt-5 vs Gemini judge
- `results/gt_audit_v2/` — the independent faithfulness audit + evidence crops
- `results/EXTRACTION_COMPARISON.md` — per-capability matrix · `results/vendor_md/<vendor>.md` — full reconstructions
- `results/COMPARISON.md` — page-classification accuracy + the **per-page speed/cost table** (source of the §6 speed column)
- `ground_truth/GROUND_TRUTH.md` — the corrected 599-page reference (v1 archived `GROUND_TRUTH_v1.md`)
- `DESIGN.md` — full methodology, bias controls, reproducibility

→ **Methodology and design rationale:** [`DESIGN.md`](DESIGN.md)
