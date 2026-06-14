# PDF Extraction Benchmark — Final Report

**Date:** 2026-06-14 · **Corpus:** 3 finance/business PDFs, 599 pages · **Approaches:** 8
**Methodology:** [`DESIGN.md`](DESIGN.md) · **Headline metric:** the *structure-aware fair total* (document-level information capture where a value counts only if its binding is recoverable) · **Metric note:** [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md)

---

## 1. Executive summary

We measured how much of a complex business document's **actual information** — text, tables, chart *data*, diagram structure, layout — each of eight extraction approaches recovers, across a 599-page corpus (a French consulting deck, an English annual report, an English investor deck). The headline is the **structure-aware fair total**: a density-weighted ratio of information captured to information present, where a value counts **only if its binding is recoverable** (which row/column/series/node it belongs to). On finance/M&A/consulting documents a number bound to the wrong row is an *active downstream error*, worse than an omission — so structure is scored, not caveated. Correct structure described in prose earns full credit; on unstructured pages the metric is plain content recall. The prior content-recall numbers are kept as a diagnostic (the **structure gap** between them is itself a vendor property). See [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md).

**The six things that matter:**

1. **Gemini 3.5 Flash wins on structure-aware capture — 89%** — at **~half the cost of gpt-5**, with low padding (8% unsupported) and the smallest structure gap of any vendor (−3). Best quality-per-dollar of any vendor that doesn't share a family with the judge.
2. **Gemini 3.1 Flash-Lite is the value shock — 86% for $1.12.** It gives up ~3 points to its bigger sibling for **~6× less money**.
3. **Structure-aware scoring is the great separator — and it sorts vendors into two classes.** Every tool that *preserves structure* (the vision LLMs, Landing AI, agentic LlamaParse) loses ≤6 pts vs its content-recall number; the two pure-text-dump tools, **PyMuPDF (84→68) and Tesseract (64→52), lose 11–16** — identically under both independent judge families. Recovering the right characters is not the same as recovering usable information.
4. **PyMuPDF is a cheap text/table first pass, not a top-tier extractor — 68%.** Its 84% content recall was inflated by structure loss: it merges side-by-side tables and destroys relational-diagram bindings (org charts, process flows). It is still excellent value for born-digital *text + simple tables* at $0, but it drops to a clear lower tier once bindings are scored. See [`AUDIT_PYMUPDF_STRUCTURE.md`](AUDIT_PYMUPDF_STRUCTURE.md).
5. **LlamaParse (agentic) and Landing AI are the coordinates-grade middle tier — 86% / 81%** — both read figures and emit exact boxes, both hold up under structure-aware scoring (small gaps), and both depend on a *config choice*: LlamaParse must run its **`agentic`** tier (the middle `accurate` tier silently dropped whole pages and scored 71%, see [`AUDIT_LLAMAPARSE_MODE.md`](AUDIT_LLAMAPARSE_MODE.md)); Landing AI carries the **highest padding (17%)**. **Tesseract (52%)** is a scanned-document last resort.
6. **The vendor ranking is robust to the metric change** — the top order holds — but the *gaps* open into clear tiers, and the headline now reflects downstream usability rather than raw token coverage.

> **Note on gpt-5 (◆).** gpt-5 built the transcription the judge grades against, so its rows (88%/87% structure-aware) are an **upper bound by construction** — reported for context, not ranked. Even so, **Gemini Flash edges it (89% vs 88%)** *despite* the twin advantage — strong evidence the residual bias is mild and the clean ranking is trustworthy (validated four ways in §9, and the structure change reproduces identically under a non-OpenAI judge).

> **Operational note — speed.** Per-page extraction latency spans **~150×**: PyMuPDF **0.11 s/page** (local) to Landing AI **16.6 s/page**. The cloud vision tier clusters at **4–7 s/page** (Gemini Flash-Lite 4.4, gpt-5-image 4.1, Gemini Flash 6.9, gpt-5-file 7.0). Latency does *not* track capture on this corpus (fastest = weakest). Full table and the two measurement caveats (Landing AI run page-by-page; LlamaParse derived) are in §6.

---

## 2. The headline — structure-aware fair total

> *How much of the document's real information did this vendor convey **with the bindings intact**?* Each vendor's full 599-page extraction was diffed page-by-page against `ground_truth/GROUND_TRUTH.md` by a blind gpt-5 judge that **credits equivalent phrasing** (a chart described in different-but-correct words, with the same numbers *and the same value↔row/series/node bindings*, counts as captured) but scores tokens whose bindings are destroyed as un-recalled. The total is **Σ(info_recall × page_info_weight) ÷ Σ(page_info_weight)**. Not a dimension average; not token overlap. The **content recall** column is the prior rubric (presence, ignoring binding); the **structure gap** between them is how much apparent capture fails a binding check.

| Rank | Vendor | **Fair total** (structure-aware) | Content recall | Structure gap | Unsupported | Cost (599pp) | Coordinates |
|---:|---|---:|---:|---:|---:|---:|:--:|
| 1 | **Gemini 3.5 Flash** | **89%** | 92% | −3 | 8% | $7.12 | coarse |
| 2 | Gemini 3.1 Flash-Lite | **86%** | 90% | −4 | 8% | **$1.12** | coarse |
| 3 | **LlamaParse** (agentic) | **86%** | 90% | −4 | 10% | paid (agentic tier) | **exact boxes** |
| 4 | **Landing AI** | **81%** | 87% | −6 | 17% | paid | **exact boxes** |
| 5 | PyMuPDF | **68%** | 84% | **−16** | 5% | **$0** | exact boxes |
| 6 | Tesseract | **52%** | 64% | **−12** | 15% | $0 | word boxes |
| ◆ | gpt-5 (image) | 88% ◆ | 91% | −3 | 9% | $13.82 | coarse |
| ◆ | gpt-5 (file) | 87% ◆ | 91% | −4 | 9% | $12.54 | coarse |

> **Scores are structure-aware (2026-06-14).** Both judge families re-judged all 599 pages with the binding-aware rubric; the change is identical across them (PyMuPDF −16 under *both* gpt-5 and Gemini). The structure-preserving vendors lose ≤6; the two character-dump tools lose 11–16. Ranking order holds, gaps open into tiers. Methodology + validation: [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md). The content-recall numbers (graded against the corrected v2 `GROUND_TRUTH.md`; see §9) are preserved in `results/_fair_total_judging_content.json`.
>
> *Two earlier fixes still hold under structure-aware scoring:* the **judge-input truncation** fix (6,000→16,000-char cap, deflated only Landing AI; [`AUDIT_VEND_CAP.md`](AUDIT_VEND_CAP.md)) and the **LlamaParse tier** fix (`accurate`→`agentic`, +18–22 pp; [`AUDIT_LLAMAPARSE_MODE.md`](AUDIT_LLAMAPARSE_MODE.md)).

**How to read the columns together:** `fair total` is *structure-aware completeness*; `content recall` is *presence ignoring binding*; their gap is *structure preservation*; `unsupported` is *fidelity* (now counting an actively wrong binding as a contradiction).
- **PyMuPDF (68% / gap −16 / 5%)** — the gap is the headline: it recovers characters but loses the structure they depend on. Its `unsupported` rises once misbinding counts (it doesn't invent text, but a flat dump strands values away from their keys).
- **Landing AI (81% / gap −6 / 17%)** — holds up reasonably on structure but carries the highest padding (verbose, occasionally interpretive ADE figure prose).
- **Gemini 3.5 Flash (89% / gap −3 / 8%)** — the best *balance*: top structure-aware capture, smallest gap, low padding.

---

## 3. Where each vendor wins and loses — structure-aware fair total by category

| Vendor | Text (149) | Table (128) | Chart (152) | Mixed (113) | Cover (55) | Image (2) |
|---|---:|---:|---:|---:|---:|---:|
| **Gemini 3.5 Flash** | 95% | **87%** | **84%** | **93%** | 84% | 82% |
| Gemini 3.1 Flash-Lite | 94% | 85% | 78% | 89% | **85%** | 68% |
| **LlamaParse** (agentic) | **96%** | 85% | 76% | 92% | 77% | 42% |
| **Landing AI** | 93% | 80% | 73% | 83% | 80% | 48% |
| PyMuPDF | 80% | 71% | 54% | 79% | 51% | 28% |
| Tesseract | 78% | 50% | 33% | 59% | 31% | 37% |
| gpt-5 (image) ◆ | 96% | 85% | 82% | 92% | 92% | 90% |
| gpt-5 (file) ◆ | 94% | 83% | 82% | 92% | 89% | 79% |

> Counts are pages per category. **Image/Photo is only 2 pages** (the corpus treats photo-filled title pages as Cover/Divider by function) — read that column as anecdote, not signal. Numbers are structure-aware (bindings required).

**The story the columns tell (now that binding is scored):**
- **Chart** is the great separator. The vision LLMs (82–84%), **LlamaParse agentic (76%)** and Landing AI (73%) read and *correctly bind* label-free bars/lines; the pure text-layer tools collapse here once geometry/series binding is required — PyMuPDF **54%** (was 79% on content alone), Tesseract 33%.
- **Table** now spreads more than it did on content recall: Gemini 87%, LlamaParse/Flash-Lite 85%, Landing AI 80%, **PyMuPDF 71%** (its side-by-side-table interleaving costs it the binding check), Tesseract 50%.
- **Text** is still solved by everyone with vision or a text layer (94–96%); PyMuPDF (80%) and Tesseract (78%) trail because some "text" pages carry callouts/columns whose order they scramble.
- **Cover/Divider** is where structure barely matters (sparse pages), so PyMuPDF (51%) is unchanged from content — its cover weakness is *visual*, not structural. The vision models handle them (80–92%).

---

## 4. The per-capability matrix (diagnostic view)

The fair total answers "how much of the document," but for *engineering decisions* you often need the per-capability picture. From `results/EXTRACTION_COMPARISON.md` (Gen-2 metrics):

| Vendor | Content recall | Numbers (finance) | Table recovery | Graph data | Diagram struct | Reading order | Coords | Cost |
|---|---:|---:|---:|---:|---:|---:|:--:|---:|
| gpt-5 (image) | 97% | 96% | 90% | 85% | 66% | 67% | coarse | $13.82 |
| gpt-5 (file) | 97% | 97% | 91% | 84% | 70% | 60% | coarse | $12.54 |
| **Gemini 3.5 Flash** | 97% | 96% | **98%** | **85%** | **91%** | 67% | coarse | $7.12 |
| Gemini 3.1 Flash-Lite | 96% | 95% | 94% | 83% | 82% | 67% | coarse | **$1.12** |
| Landing AI | 95% | 93% | 91% | 80% | 82% | 63% | **exact** | paid |
| **LlamaParse** (agentic) | 97% | 97% | 98% | 77% | 83‡ | 69% | **exact** | paid |
| PyMuPDF | 97% | 97% | 57% | 29% | 29% | **90%** | **exact** | $0 |
| Tesseract | 88% | 72% | 0% | 24% | 29% | 68% | word | $0 |

Two reading notes carried from the methodology:
- **‡ LlamaParse diagram structure** is shown as the **element-level** judge's score (83), not the figure judge's (30). The figure judge reads only *figure-typed* blocks, but LlamaParse-agentic delivers diagram content as **inline markdown prose** — so the figure judge under-counts it while the element-level judge (reading its full markdown) credits it. Its graph-data 77 (up from 44 at the accurate tier) is the figure judge's. See the caveat in [`results/EXTRACTION_COMPARISON.md`](results/EXTRACTION_COMPARISON.md).
- **Reading order** is Kendall-τ vs a text-layer reference; **PyMuPDF's 90% is inflated** because the reference uses the same layout engine. Treat it as a capability flag (parsers emit exact element order), not a ranking.
- **Content/numeric recall saturate** at 95–97% — they cannot discriminate the serious vendors, which is *why* the structure-aware fair total exists. These per-capability dimensions (**table recovery, graph data, diagram structure**) already price structure, and they corroborate the headline change exactly: the tools that crater on them (PyMuPDF graph-data 29, diagram-struct 29, table-recovery 57; Tesseract worse) are precisely the two that lose 11–16 pts when the fair total goes structure-aware. The structure-aware fair total spread among real vendors is now ~37 pp (Tesseract 52 → Gemini Flash 89) vs ~2 pp for token recall.

> **Gemini 3.5 Flash is the standout on the figure dimensions** — top-tier graph-data fidelity (85%, level with gpt-5's 84–85%) and a commanding diagram-structure lead (**91%** vs gpt-5 66–70%, Landing AI 82%) — at half gpt-5's cost. This is the single biggest capability finding in the matrix.

---

## 5. The table-recovery correction (the question that started this)

This entire deep-dive began with a correct instinct: *"Landing AI's table extraction at 60% — I don't buy it."* It was right.

| | Landing AI table score |
|---|---:|
| Original metric (`table_presence_legacy`) | **56%** ❌ |
| Corrected metric (`table_recovery`) | **91%** ✅ |

**The 56% was a metric artifact, not a Landing AI weakness and not a ground-truth error.** Two bugs:

1. **Collector dropped figure-embedded tables.** Landing AI's ADE classifies a table that contains a logo/photo/icon as a `figure` chunk — whose text nonetheless holds the *full table*. The collector only counted literal `table` chunks, silently discarding those tables. *Fixed:* detect figure-embedded tables structurally (requires the word "table" **and** bullets/pipes/digits).
2. **Denominator demanded a table where none existed.** The metric required a table on every `Table`∪`Mixed` page, but ~half of `Mixed` pages are chart+text with no table. That punished Landing AI's *correct abstention* and rewarded over-emission (the accurate-tier LlamaParse emitted a table on every no-table Mixed page checked; agentic LlamaParse instead tabulates real chart data). *Fixed:* score only the 128 true `Table` pages.

A tree-wide audit of the other collectors confirmed **no analogous bug**. The correction is the reason the headline can place Landing AI in the high-quality tier (87% content recall / 81% structure-aware), not the 60%-tier the artifact suggested.

---

## 6. Cost and speed — the operational axes

| Vendor | Cost / 599pp | Speed (s/page) | Fair total (structure-aware) | $ per point of capture |
|---|---:|---:|---:|---:|
| PyMuPDF | $0 usage¹ | **0.11** | 68% | $0¹ |
| Gemini 3.1 Flash-Lite | $1.12 | 4.4 | 86% | ~$0.013 |
| Gemini 3.5 Flash | $7.12 | 6.9 | 89% | ~$0.080 |
| gpt-5 (file) ◆ | $12.54 | 7.0 | 87% ◆ | ~$0.144 |
| gpt-5 (image) ◆ | $13.82 | 4.1 | 88% ◆ | ~$0.157 |
| LlamaParse (agentic) | paid (agentic tier) | 1.3 ‡ | 86% | — |
| Tesseract | $0 | 1.2 | 52% | $0 |
| Landing AI | paid (per-page) | 16.6 † | 81% | — |

**The cost curve is brutally clear:** spending more than Gemini Flash-Lite buys *diminishing returns*. Flash-Lite captures **86%** (structure-aware) for **$1.12**; gpt-5 reaches only **87–88%** (and only as an upper-bound ◆) for **11–12× the price**. Gemini 3.5 Flash is the sensible top — **89% at $7.12, half of gpt-5, and it edges gpt-5's own upper-bound rows** while leading on diagram structure. There is no quality argument for gpt-5 on this corpus that survives the price tag. Note that PyMuPDF's "free" value proposition weakens once structure is scored (68%, not 84%) — it is free for *text + simple tables*, not for figures or complex layouts.

**Speed reads the opposite way from quality.** The fastest tool is the cheapest-and-weakest (PyMuPDF, **0.11 s/page**, local) and the slowest is a paid high-quality tier (Landing AI, **16.6 s/page**) — so on this corpus latency does *not* buy capture. The cloud vision models cluster at **4–7 s/page** regardless of vendor; among them the cheaper Gemini Flash-Lite (4.4 s) is also *faster* than its bigger sibling (6.9 s), and gpt-5-image (4.1 s) is the quickest LLM. Three measurement caveats matter before trusting these:
- **Per-page mean, not whole-corpus runtime.** Every cloud vendor ran under 4–8 concurrent workers, so wall-clock for the full corpus ≈ (s/page × 599) ÷ workers. Only the **per-page mean** is a clean cross-vendor comparison; the implied totals are not.
- **† Landing AI is penalized by the harness.** It is natively a whole-document ADE but was driven **page-by-page** here (render → one POST per page), so 16.6 s/page eats per-page network + retry overhead on every call and **overstates its production latency** — run whole-doc it is materially faster.
- **‡ LlamaParse's figure is derived, not measured.** Its API is a whole-document async job; 1.3 s/page is the doc-level wall time amortized over pages (`_wall_s ÷ page_count`), not a per-page latency comparable to the others' per-call measurements.

Local tools (PyMuPDF, Tesseract) have no network in the loop; the cloud numbers include network, queueing, and retry backoff. Source: per-page `seconds` recorded for all 599 pages in each vendor's `results/_*_solution.json` (and the Gemini `_extract.json` files), summarized in [`results/COMPARISON.md`](results/COMPARISON.md).

> ¹ **PyMuPDF is not free for enterprise/proprietary use.** The $0 above is the *usage* cost (no API fee); the **license** is dual **AGPL-3.0 or a paid Artifex commercial license**. AGPL's network-copyleft (§13) means a proprietary or SaaS product must release its *entire* source under AGPL or buy a commercial license — so PyMuPDF's true cost in a typical enterprise is a license negotiation, not $0. Genuinely permissive text-layer alternatives: **pdfplumber (MIT)**, **pypdf (BSD)**. **Tesseract is Apache-2.0** — its $0 *is* license-free. Treat "free text-layer parser" in this report as "PyMuPDF *or a permissive equivalent*"; the structure-aware capture numbers (68% etc.) are properties of the text-layer-extraction *class* and carry over to pdfplumber/pypdf, which are the deploy-anywhere choices.

---

## 7. Per-vendor profiles

**Gemini 3.5 Flash — the recommended default.** Top structure-aware capture (89%, smallest gap −3), best-in-class diagrams (91% diagram-structure) and top-tier charts (85% graph-data), excellent image description, low padding (8%), $7.12. Weakness: coarse coordinates only (no element boxes), and one runaway-repetition empty page in 599 (a minor robustness ding). *Use it for almost everything.*

**Gemini 3.1 Flash-Lite — the value champion.** 86% (structure-aware) for $1.12 — within ~3 points of its big sibling at a sixth of the cost. Slightly weaker on charts. *Use it at scale, or as the figure-extraction half of a hybrid (§8).*

**Landing AI — the coordinates-grade specialist.** 81% structure-aware (gap −6, holds up reasonably), 91% table recovery, and — uniquely among the high-quality tier — **exact element bounding boxes**. Weaknesses: highest padding (17% — verbose, occasionally interpretive figure prose) and a residual gap on charts. *Use it when you need precise layout grounding / element coordinates, enterprise document workflows, or auditable region-level provenance — things no LLM gives you.*

**PyMuPDF — the cheap text/table first pass (not a top-tier extractor; AGPL-licensed).** **68% structure-aware** (84% content recall — a **−16 structure gap**, the largest of any vendor) for $0 *usage*. Perfect text and decent simple tables, but it recovers characters while losing the structure they depend on: it **merges side-by-side tables and destroys relational-diagram bindings** (org charts, process flows), and is blind to chart geometry (29% diagram structure). The structure-aware re-judge under *both* judge families drops it identically (84→68), and its `unsupported` rises once misbinding counts. Collapses entirely on scanned documents. **License caveat:** PyMuPDF is **AGPL-3.0 or a paid Artifex commercial license** — *not* free for proprietary/SaaS deployment (see cost-table note ¹). For born-digital text extraction with a permissive license, **pdfplumber (MIT) / pypdf (BSD)** occupy the same tier without the copyleft. See [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md), [`AUDIT_PYMUPDF_STRUCTURE.md`](AUDIT_PYMUPDF_STRUCTURE.md). *Use a text-layer parser as a near-free first pass for born-digital text + simple tables, then escalate figures/diagrams/complex tables to an LLM.*

**LlamaParse (agentic) — the coordinates-grade all-rounder.** In its most capable `agentic` tier (an LVM agent loop), 86% structure-aware (gap −4, holds up), perfect text (96%), strong tables, and — unlike the pure text-layer parsers — it **reads figures** with bindings intact: charts 76% and diagrams 83% (element-level), plus **exact element bounding boxes**. *Use it when you want both figure comprehension and coordinate-level provenance in one paid parser.* **Critical:** this requires the **`agentic` tier** — the middle `accurate` tier silently drops whole born-digital pages and scores only 71% (see [`AUDIT_LLAMAPARSE_MODE.md`](AUDIT_LLAMAPARSE_MODE.md)). Choosing the tier is the single biggest LlamaParse decision.

**Tesseract — scanned-document last resort.** 52% structure-aware (gap −12), 0% structured tables, 72% numeric recall (OCR drops digits). *Use it only when there is no text layer and no budget for a vision model.*

**gpt-5 (image/file) ◆ — reference-grade, not cost-justified here.** 87–88% (upper bound, gap −3/−4), but $12–14 and *behind Gemini on diagram structure and edged by Gemini Flash on the structure-aware total*. *Worth it only if you specifically need the OpenAI ecosystem; otherwise Gemini Flash dominates on price and figures.*

---

## 8. Recommendations by use case

| If you need… | Use | Why |
|---|---|---|
| **Best overall extraction, sane budget** | **Gemini 3.5 Flash** | 89% structure-aware capture, best figures, $7.12, low padding |
| **Extraction at massive scale / lowest cost with quality** | **Gemini 3.1 Flash-Lite** | 86% for $1.12 — the value frontier |
| **Exact element coordinates / layout provenance** | **Landing AI** or **LlamaParse (agentic)** | the two high-quality tiers with exact boxes; LlamaParse also reads figures; Landing AI emits a single whole-doc ADE pass (the 16.6 s/page in §6 is the page-by-page harness, not its native latency †) |
| **Figure comprehension + coordinates in one paid parser** | **LlamaParse (agentic)** | 86% structure-aware, reads charts/diagrams with bindings, exact boxes — but you must select the agentic tier |
| **Near-free text + *simple* tables on born-digital PDFs** | **A text-layer parser** (pdfplumber/pypdf if you need a permissive license; PyMuPDF only if AGPL-compliant or licensed), escalate figures/diagrams/complex tables to an LLM | $0 usage, perfect text layer — but loses structure on charts, relational diagrams, and side-by-side tables; mind PyMuPDF's AGPL license (note ¹) |
| **Maximum fidelity, cost no object, OpenAI stack** | gpt-5 (file) | reference-grade (but Gemini matches it cheaper) |
| **Scanned documents, no text layer** | a vision LLM (Gemini) or Landing AI; Tesseract only as floor | text-only tools collapse without a text layer |

**The hybrid worth building:** **a text-layer parser for text + simple tables, Gemini 3.1 Flash-Lite ($1.12) for the figure/diagram/complex-layout pages.** (Use **pdfplumber/pypdf** for the text-layer half if you need a permissively-licensed, deploy-anywhere stack; PyMuPDF is faster but AGPL — note ¹.) The text layer is unbeatable value where structure is simple; routing the chart/diagram/multi-table/image pages to a cheap vision model patches its structure blind spot — plausibly approaching top-tier capture for a few dollars per document. The structure-aware numbers make the routing boundary sharper: send anything with bindings (charts, org charts, side-by-side tables) to the LLM.

> **The born-digital caveat that changes everything for scanned docs:** all three test PDFs have a clean text layer, which is *why* PyMuPDF reaches even 68% at $0 usage (license caveat ¹) and content recall saturates. **On scanned or photographed documents the text-layer floor disappears** — PyMuPDF would crater, Tesseract's OCR errors would dominate, and the gap between the vision LLMs / Landing AI and everything else would widen sharply. Choose accordingly: the rankings above are for born-digital documents.

---

## 9. Ground-truth validation — what we stress-tested and what we changed

The benchmark's foundation is `GROUND_TRUTH.md`, a 599-page transcription **built by gpt-5** and judged by a **gpt-5** judge. That twin co-location is the one place a shared blind spot could corrupt every number, so we attacked it on three independent axes. Full detail: [`GT_VALIDATION.md`](GT_VALIDATION.md). **We did not just confirm the reference — we found real defects, corrected them, and re-measured.**

**1. Independent faithfulness audit (Claude, a different model family).** A **36-page chart-weighted** sample (3.4× the original check), every flagged page re-verified by hand at high zoom. Result: **30 faithful, 2 minor, 4 *material* defects — all four on dense multi-series figures** (e.g. SOTER p30, where gpt-5 replaced 17 of 21 *printed* ARPU labels with a smoother invented series; p102, a subscriber chart whose (2.2) churn bar was omitted). An earlier "16/16 faithful" spot-check had simply not sampled the hard figure pages. Text, prose, and financial tables remained faithful — including arithmetic-checkable statements (IAR p258/p265 foot internally and tie cross-page: profit-before-tax **48,937** appears identically on both).

**2. The root cause, and the fix.** All three PDFs are born-digital, so every printed number lives in the **text layer** — an exact, vision-free oracle. A text-layer diff over all 599 pages put v1 printed-number fidelity at **97.5% on charts / 98.4% overall** (the GT was far better than the worst pages implied), but the figure errors were real and, crucially, **biased the benchmark *against* the text-layer parsers**: a vendor that correctly read `185, 184, 201` was scored as *disagreeing* with gpt-5's hallucinated `165, 166, 135`. We rebuilt all 275 figure pages with the **authoritative text layer + a 2400px render** (`build_gt_md_v2.py`), raising printed-number fidelity to **99.1% charts / 99.5% overall** and fixing every audited defect. This corrected `GROUND_TRUTH.md` is now canonical (v1 archived as `GROUND_TRUTH_v1.md`).

**3. Re-measure — does the correction move the ranking?** Same vendors, same judge, only the corrected reference. **The ranking is identical.** But the fix removed exactly the twin bias: on chart pages the text-layer vendors gained most (**PyMuPDF +7.6, LlamaParse +6.4, gpt-5-file +4.4**) while **gpt-5-image — the one model sharing the GT's blind spot — was the only vendor that did not improve (−0.2)**. That file-gains/image-flat split is direct evidence the effect was real and is now corrected.

**4. Cross-family judge.** Re-judging the corrected GT with a non-OpenAI judge (**Gemini 3.5 Flash**, byte-identical prompt/shuffle) keeps the **same top set with Gemini Flash #1 under both judges**, and confirms the agentic-tier LlamaParse re-run (next note) in the top cluster under both families. Neither judge favours its own family (the Gemini judge scores gpt-5-image level with its own Gemini Flash). See [`results/FAIR_TOTAL_JUDGES.md`](results/FAIR_TOTAL_JUDGES.md).

> **Note — §9 is about GT *content* fidelity, and predates two later changes.** It validates that the ground-truth transcription has the right *numbers* (a text-layer-anchored correctness check), which is orthogonal to — and still holds under — the structure-aware metric: structure-aware scoring re-judges vendors against the *same* corrected GT. The re-measure deltas quoted here (e.g. PyMuPDF +6.4 on charts) are **content-recall-era** numbers run with the original **accurate-tier** LlamaParse. The agentic-tier re-run ([`AUDIT_LLAMAPARSE_MODE.md`](AUDIT_LLAMAPARSE_MODE.md)) and the structure-aware re-judge ([`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md)) are the two later changes; both reproduce under both judge families.

**Conclusion:** the v1 reference was sound on the born-digital majority but had a real, *correctable* error rate on dense figures that mildly **flattered the image-mode LLMs**. Corrected and re-measured, the **ranking holds and the numbers are more accurate**. *(Layer 1, the category key, was separately audited via gpt-5 third-vote triangulation — `results/GROUND_TRUTH_AUDIT.md` — and found sound.)*

---

## 10. Caveats

1. **Born-digital corpus.** All three PDFs have clean text layers; rankings would shift on scanned documents (§8).
2. **gpt-5 is transcriber and judge.** The reference was independently audited (Claude), found to have material defects **only on dense figures**, **corrected** via a text-layer-anchored rebuild, and the ranking confirmed stable under both the corrected GT and a non-OpenAI (Gemini) judge (§9). gpt-5's own rows are flagged ◆ and excluded from the ranking.
3. **Chart data is inherently estimated** for label-free figures; those scores carry more uncertainty than table scores (printed labels are now anchored to the text layer; only genuinely unlabeled geometry remains estimated).
4. **Single judge pass**, not a panel — stabilized by blind shuffling and the contradiction-only fidelity definition.
5. **n = 3 documents** (599 pages) — trust the wide gaps most, the within-few-points gaps least.
6. **Costs are point-in-time** on this corpus; Landing AI's dollar figure was not captured (`paid`).
7. **Judge-input length (audited & fixed).** Vendor text and the GT reference are fed to the judges at no-truncation caps on this corpus. An earlier 6,000-char/page cap deflated only Landing AI (longest output) in the fair-total and element evals; the figure judge had per-figure/blob caps (1,600/7,000) that mildly clipped Landing AI and gpt-5. Both were corrected pre-publication and re-judged — fair-total/element moved Landing AI +2–13pt, the figure dimensions ±≤3pt (Landing AI diagram-struct 79→82) — **no ranking changed in any eval**. Full trail: `AUDIT_VEND_CAP.md`.
8. **Vendor tier/mode is a first-class variable (audited & fixed).** LlamaParse was originally run in its middle `accurate` tier, which silently dropped whole born-digital pages; re-running at its most capable `agentic` tier lifted it +18.5/+21.8 pp (both judge families, weights fixed) into the top cluster — **this is the canonical result** and it *did* change LlamaParse's rank (8th→3rd among real vendors). Lesson: benchmark every vendor's most capable documented mode. Full trail: `AUDIT_LLAMAPARSE_MODE.md`. The figure judge under-counts LlamaParse-agentic's diagrams (delivered as inline markdown, not figure blocks); the element-level judge (diagrams 83) is the fair measure.
9. **Structure is now scored, not caveated (resolved 2026-06-14).** The earlier content-recall rubric credited *information present* regardless of whether its binding survived, which inflated the pure-text-dump tools. The headline fair total is now **structure-aware** — a value counts only if its row/column/series/node binding is recoverable, and an actively wrong binding counts as a contradiction. Re-judged across all 599 pages under **both** judge families: PyMuPDF 84→**68**, Tesseract 64→**52**, every structure-preserving vendor ≤6 pp; the change is identical across families. Content recall is retained as a labeled diagnostic and the **structure gap** is reported per vendor (§2). Full methodology: [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md); origin audit: `AUDIT_PYMUPDF_STRUCTURE.md`.
10. **Speed is per-call latency under concurrency — recorded, not headline (§6).** Per-page extraction `seconds` is logged for all 599 pages, but it is per-call wall time measured with 4–8 concurrent workers, so it is **not** whole-corpus runtime. Two vendors' figures are not directly comparable to the others': **Landing AI** was driven page-by-page (overstating its native whole-doc latency, †) and **LlamaParse**'s per-page number is doc-level async time amortized over pages (‡). Local tools (PyMuPDF/Tesseract) exclude network. Treat the per-page mean as the comparable signal and the wide gaps (≈150× from local to Landing AI) as the takeaway; speed is an operational axis, deliberately kept out of the capture-quality headline.

---

## 11. Appendix — corpus & artifacts

**Corpus:** `20190308_Projet_Alpha_Restitution` (156pp, French consulting deck) · `IAR_FY25_EN` (310pp, English annual report) · `SOTER - Company Presentation - vFF` (133pp, English investor deck). 599 pages total.

**Ground-truth build:** `GROUND_TRUTH.md` (v1) — gpt-5 vision, 1,502,226 chars, **$22.18**, 0 empty pages. **Correction (v2, now canonical):** 275 figure pages rebuilt with the authoritative text layer + 2400px render, **$11.77**; printed-number fidelity 98.4%→99.5% (§9). Fair-total judge — gpt-5, **$12.67/run** (v1 + v2); cross-family Gemini judge **$7.05**.

**Key artifacts:**
- [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md) — **the canonical metric definition**: why and how scores are structure-aware (bindings required), content-vs-structure under both judge families, per-category validation
- `results/FAIR_TOTAL.md` — headline metric (structure-aware; content recall + structure gap columns)
- `GT_VALIDATION.md` — the three-axis ground-truth validation (audit → correction → re-measure → cross-family judge)
- `AUDIT_VEND_CAP.md` — the pre-publication judge-harness audit: the VEND_CAP truncation artifact found, fixed, and re-measured under both judge families (+ completeness, bootstrap CIs, sensitivity)
- `AUDIT_LLAMAPARSE_MODE.md` — the LlamaParse tier audit: benchmarked `accurate` vs the canonical `agentic` tier (+18.5/+21.8 pp), comparison-plumbing + GT-fairness checks, both judge families
- `results/BY_DOCUMENT.md` — results sliced by document **genre** (annual report / M&A info memo / French consulting report): fair-total by doc and by category×doc, both judge families. The annual report is the easy genre; the chart-heavy M&A memo is the great vendor separator (`scripts/by_document.py`)
- `AUDIT_PYMUPDF_STRUCTURE.md` — the PyMuPDF structure audit: content recall over-credits structure loss for pure-text-dump tools; controlled structure-strict re-judge isolates it (PyMuPDF −24.5 pp on diagram pages vs ≤5 pp for structure-aware vendors; rank holds)
- `results/vendor_md/README.md` — per-vendor ground-data manifest (8 byte-faithful single-md extractions, 599 pages each; LlamaParse = agentic)
- `results/FAIR_TOTAL_V1_V2.md` — pre/post-correction deltas · `results/FAIR_TOTAL_JUDGES.md` — gpt-5 vs Gemini judge
- `results/gt_audit_v2/` — the independent faithfulness audit + evidence crops
- `results/EXTRACTION_COMPARISON.md` — per-capability matrix · `results/vendor_md/<vendor>.md` — full reconstructions
- `results/COMPARISON.md` — page-classification accuracy + the **per-page speed/cost table** (source of the §6 speed column; raw per-page `seconds` stored in each `results/_*_solution.json`)
- `ground_truth/GROUND_TRUTH.md` — the corrected 599-page reference (v1 archived `GROUND_TRUTH_v1.md`)
- `DESIGN.md` — full methodology, bias controls, reproducibility

→ **Methodology and design rationale:** [`DESIGN.md`](DESIGN.md)
