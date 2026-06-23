# How Enterprise Data Teams Should Approach PDF Data Extraction

> **Scoring is structure-aware as of 2026-06-14** ([`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md)):
> a value counts only if its binding survives, because a number under the wrong row is a downstream
> error. This sharpens the playbook's core point — character extraction ≠ usable structure. Headline
> figures shift accordingly (PyMuPDF 84→68; the structure-preserving vendors move ≤6).

**A solution-consultant playbook.** Date: 2026-06-13.
**Audience:** enterprise data, platform, and ML teams choosing how to extract structured data from PDFs at scale.
**Evidence base:** the benchmark in this repo (8 extraction approaches, 599 pages, finance/business documents) — see [`FINAL_REPORT.md`](FINAL_REPORT.md), [`DESIGN.md`](DESIGN.md), and the measurement-integrity audit in [`AUDIT_VEND_CAP.md`](AUDIT_VEND_CAP.md). Scope caveat: the corpus is **born-digital finance/business** documents; the *structural* findings transfer broadly, the *exact vendor scores* do not.

---

## The thesis

**Don't start by picking a vendor. Start by segmenting your documents, then match a *tool class* to each segment — and architect a cheap router, not a single golden parser.** The most common enterprise mistake is treating "PDF extraction" as one procurement decision with one winner. This benchmark showed the #1 vendor *flips with document mix*, and a single measurement bug moved a vendor 13 points. Ranking is content-dependent; treat it that way.

---

## Step 1 — Segment your document estate (this fork decides everything)

Before evaluating anything, profile your corpus on three axes:

| Axis | Why it dominates the decision |
|---|---|
| **Born-digital vs scanned/photographed** | The single biggest fork. Born-digital PDFs carry an exact text layer → free tools nail text & numbers. Scanned/photographed → that floor disappears; you *need* vision/OCR. This benchmark was 100% born-digital — its rankings do **not** transfer to scanned docs. |
| **Text/table-heavy vs figure-heavy** | Plain text & born-digital tables are essentially solved by everyone (~95%+). **Charts and diagrams are the great separator** — *figure-reading* tools (vision LLMs, and document-AI parsers in their agentic/LVM tiers) score ~83–92%; *pure text-layer* tools (PyMuPDF, plain OCR) score ~45–50%. If your value is in figures, this is where money — and picking the right *tier* — buys quality. |
| **Fixed-template vs free-form** | Invoices/KYC/forms with stable layouts favor template / document-AI extractors with field-level confidence. Free-form reports/decks favor general vision or holistic parsers. |

Most enterprises find their estate is 70–80% "born-digital, text/table-heavy, semi-structured" with a long tail of scanned and figure-heavy documents. **That distribution, not a leaderboard, dictates architecture.**

---

## Step 2 — Know the four tool classes (not the brands)

| Class | Examples | Strengths | Weaknesses | Use when |
|---|---|---|---|---|
| **Native-vision LLM** | Gemini Flash, GPT‑5 / Claude vision | Best all-round; reads charts/diagrams; paraphrase-robust | No exact coordinates; per-page cost; **can hallucinate plausible-but-wrong values**; model drifts under you | Mixed/unknown, figure-heavy, scanned |
| **Document-AI parser** | Landing AI ADE, **Mistral OCR**, LlamaParse, Azure Document Intelligence, AWS Textract, Google Document AI | **Exact bounding boxes / provenance**, table structure, scale, in-tenant deployment; **their top "agentic"/LVM tiers now read charts & diagrams at near-vision quality** | Per-page cost; **basic/default tiers trail badly on figures and can silently drop pages** — you must select the most capable tier; **and that capable tier can over-assert or even *fabricate* figure prose** (Mistral OCR 4's advanced chart-annotation layer reads charts yet invents content on graphics it can't parse — 19% unsupported, the highest in this benchmark; surface confidence scores and verify figure-derived claims) | You need coordinates, auditability, compliance, fixed forms |
| **Text-layer extractor** | pdfplumber (MIT), pypdf (BSD), **PyMuPDF (AGPL-3.0 ⚠)** | ~Perfect text+tables on born-digital, $0 *usage*, instant, **never invents** | Blind to figure geometry; returns nothing on scanned pages; **PyMuPDF is AGPL/commercial — not free for proprietary use (see License gate, Step 6)** | Born-digital bulk; the cheap first pass |
| **OCR** | Tesseract (+ cloud OCR) | Reads rendered text with no text layer | Error-prone on **numbers** (finance risk); no structure | Scanned, no budget — a floor, not a finish |

Within the vision class, this benchmark's corrected numbers (finance/business, born-digital) put **Gemini 3.5 Flash** as the best generalist-per-dollar, with GPT‑5 / Claude as a reference tier and **Gemini Flash-Lite** as the value option — but treat that as one evidence point, not gospel.

---

## Step 3 — The reference architecture: a confidence router, not one parser

The cost-and-quality-optimal pattern for a heterogeneous estate is almost never a single vendor:

```
        ┌─ born-digital text/tables ──► text-layer parser (0% hallucination)
        │                               pdfplumber/pypdf = permissive; PyMuPDF = AGPL ⚠
PDF ──► classify page ─┼─ figures / charts / diagrams ──► vision LLM (e.g. Gemini Flash)
        └─ scanned / no text layer ───► vision LLM or cloud Document-AI
                                              │
                              low-confidence / high-stakes field
                                              ▼
                                   human-in-the-loop review (with coordinates)
```

- A cheap deterministic first pass handles the 70–80% that's born-digital text — at $0 and zero invention.
- You pay the vision premium **only** on pages that need eyes (figures, scans, low confidence).
- This typically cuts cost by an order of magnitude versus "send everything to an LLM" while *raising* quality on the hard pages.

---

## Step 4 — Optimize for fidelity and provenance, not just recall

For finance, legal, and regulated workflows this is the point most leaderboards miss:

- **A parser that pads with confident-but-wrong numbers is more dangerous than one that omits.** Measure *hallucination / unsupported* as a separate axis from recall. In this benchmark the most "complete" parser also asserted the most unsupported content (~17%) — completeness and fidelity are different columns; read both.
- **Coordinates = auditability.** If a human or auditor must trace an extracted figure back to the page, you need bounding boxes — which the LLM class doesn't provide. That alone can decide vision-LLM vs document-AI regardless of accuracy.
- **Numbers are the crown jewels.** OCR mangles digits; even vision models *estimate* label-free chart values. Wherever a number drives a downstream decision, gate it: validation rules, cross-footing/arithmetic checks, dual-extraction agreement, or human review.

---

## Step 5 — The non-negotiable: build a small ground-truth eval on *your* documents

The highest-leverage thing a data team can do, and the meta-lesson of building this benchmark:

- **Leaderboards don't transfer.** The same vendor scored 94% on an annual report and ~79% on chart decks; "who's #1" inverted with corpus mix and with which vendors were in the race.
- **Measurement is treacherous.** Building this benchmark surfaced a 6,000-char input cap that silently deflated the most verbose vendor by up to 13 points, a metric whose denominator punished correct abstention, and a ground truth that *itself* hallucinated chart numbers. If you don't audit your eval, your eval will lie to you.
- **Benchmark each vendor's *most capable tier* — tier choice can dwarf vendor choice.** One parser scored 71% in its default/middle tier (it silently dropped whole pages) and **90%** — a different league, and a different rank — in its top "agentic" tier. Same product, same API, one parameter. Pin the tier/model explicitly, confirm it in the response metadata, and re-confirm when the vendor changes defaults. A "vendor is weak" conclusion drawn from the wrong tier is the most expensive eval mistake you can make.

So: assemble **50–150 pages representative of your real estate** (include your messy tail), define what "correct" means *for your use case* (text? numbers? table structure? chart data? coordinates?), hand-label a gold set, and score 2–3 candidates blind. Re-run when your documents or the vendor's model change. A few engineer-days here beats any analyst report — including this one.

---

## Step 6 — The enterprise gates that override accuracy

Accuracy rankings are moot if a tool fails a hard constraint. Check these *first*:

- **Open-source license / IP** — *a "$0" tool is not necessarily a free one.* The most-cited free text-layer parser, **PyMuPDF (`fitz`), is AGPL-3.0 or a paid Artifex commercial license**. AGPL's network-copyleft (§13) means that embedding it in a proprietary or SaaS product obliges you to release your *entire* application's source under AGPL — or to buy a commercial license. For most enterprises that is a hard no on the AGPL path, so PyMuPDF's real cost is a commercial-license negotiation, not $0. If you want genuinely permissive, deploy-anywhere text extraction, prefer **pdfplumber (MIT)** or **pypdf (BSD)**; **Tesseract is Apache-2.0**. Audit the license of *every* library in the pipeline before architecting around its "$0" price.
- **Data residency / security** — can documents leave your tenant? Many can't. This rules out public-API LLMs and pushes you toward in-VPC cloud Document-AI (Azure/AWS/GCP) or self-hosted models, *regardless* of benchmark scores.
- **Latency & throughput at volume** — per-page vision calls and rate limits matter at millions of pages; the free text-layer first pass is also your throughput lever.
- **Model versioning & reproducibility** — hosted models change underneath you; pin versions, snapshot eval results, and re-test on upgrades.
- **Total cost at scale** — output tokens dominate LLM cost; a router that reserves vision for the hard pages is the main cost control.

---

## The one-paragraph answer for an executive

> Treat extraction as a routing problem, not a vendor bake-off. Segment documents by digital-vs-scanned and text-vs-figure; run a low-cost text-layer parser over the born-digital bulk (pick a permissively-licensed one — pdfplumber/pypdf — since the popular PyMuPDF is AGPL and not free for proprietary use), escalate only figures, scans, and low-confidence pages to a vision model; keep humans on high-stakes numbers with coordinate-level provenance. Choose the specific tools by running a ~100-page eval on your own documents — because rankings are corpus-dependent and the measurement is the hard part — and respect data-residency *and library-license* constraints before accuracy. Budget for re-evaluation, not a one-time decision.

---

## Quick-reference decision guide

| If your documents are… | Start with | Why |
|---|---|---|
| Born-digital, text/table-heavy (reports, statements) | Text-layer parser (pdfplumber/pypdf = permissive; PyMuPDF only if AGPL-compliant or licensed), escalate exceptions | ~perfect text+tables, $0 usage, never invents — but check the license (Step 6) |
| Figure / chart / diagram-heavy (decks, infographics) | Native-vision LLM, or a document-AI parser's agentic/LVM tier | figure-reading tools score ~83–92% vs ~45–50% for pure text-layer parsers |
| Scanned / photographed (no text layer) | Vision LLM or cloud Document-AI; OCR as floor | text-layer parsers return nothing |
| Fixed-template forms (invoices, KYC) | Document-AI with field confidence | template + field-level scoring + provenance |
| Compliance / audit / coordinates required | Document-AI (exact boxes) | LLMs don't emit bounding boxes |
| Cannot leave the tenant | In-VPC cloud Document-AI or self-hosted model | data residency overrides accuracy |
| Mixed / unknown estate | A router across the above + your own eval | no single tool wins across segments |
