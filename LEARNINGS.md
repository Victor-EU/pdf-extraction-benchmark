# Learnings — what two PDF-extraction benchmarks teach together

*Synthesis of the **Finance** benchmark (this repo — 599 pages, 3 born-digital business documents) and its sibling the **Insurance** benchmark (`../PDF parsing test - Insurance` — 7 pages, 2 French forms). Both use the same structure-aware metric, the same two judge families, and mostly the same vendors, so the second corpus acts as an independent replication of the first in a different genre.*

> **One-line synthesis.** Document extraction is not a tool you pick once — it is a *routed, verified capability*. There is no "best parser"; there is a function of **(document genre × which binding carries the value × downstream stakes)**. Route by where the value lives (text-layer tools for born-digital prose/tables; a vision model the moment pixels matter), verify high-stakes fields deterministically and with a second model, and evaluate on "is the binding recoverable" with a cross-family judge on a corpus large enough to clear the ±20 pp noise floor.

---

## 1. The two benchmarks, and why combining them is legitimate

|  | **Finance** | **Insurance** |
|---|---|---|
| Corpus | 599 pp, 3 born-digital docs (FR consulting, EN annual report, M&A memo) | 7 pp, 2 French forms (employer attestation + social-aid demande) |
| What a "binding" is | row / column / chart-series / diagram-node | form-field / **checkbox** / table-cell |
| Ground-truth author (◆, unranked) | **gpt-5** | **Gemini 3.5 Flash** |
| Clean #1 | **Gemini 3.5 Flash** (89) | **Mistral OCR 4** (92) — Pulse 90, gpt-5 (image) 80 |
| Headline metric | structure-aware fair total = Σ(recall × page-weight) / Σ(page-weight); a value counts only if its binding is recoverable | identical |
| Judges | gpt-5 + Gemini 3.5 Flash (cross-family) | identical |

**The honest kind of combination is replication, not pooling.** You cannot average 599 + 7 pages into one score — the result would just be Finance, the ◆ ground-truth roles differ between the two, and the 7-page corpus carries ±20–25 pp per-page judge noise. The value of the second corpus is that it tests whether Finance's central claims survive a completely different document genre, language mix, and binding type, under two independent judges. They do — and that is the strongest external-validity evidence the project has.

---

## 2. What replicates across both corpora (the load-bearing findings)

### 2.1 The structure-gap thesis replicates — and amplifies
The most important Finance claim is that text-dumpers recover *characters* but lose *structure*, so content-recall flatters them and structure-aware scoring is the honest cut. This reproduces exactly on a different genre, and the gap *widens* because a form has no easy prose to hide in:

| Tool | structure gap, Finance | structure gap, Insurance (forms) |
|---|---:|---:|
| PyMuPDF | −16 | **−23** |
| Tesseract | −12 | **−15** |

On the insurance form PyMuPDF scores a perfect **100% on the objective text-layer-reference dimension** (every text-layer character recovered; the LLM-judge content diagnostic reads 71%) yet only **49% structure-aware** — it emits a flat run of labels followed by a separate run of values, so "SIRET = 33369592200414" is destroyed and checkbox state is absent entirely. A finding that holds across 599 business pages *and* 7 dense forms, under two judge families each, is not a corpus artifact.

### 2.2 The separator is always the non-textual datum
What separates good from bad extraction is always the information that lives in **pixels / 2-D position**, never in the character stream:

- **Finance:** chart-data fidelity. The chart-heavy M&A memo spread vendors **40–47 pp**; the prose annual report compressed them into a ~1 pp band.
- **Insurance:** checkbox state. *Which box is ticked* — the single most consequential datum on a benefit form — is captured at **0%** by the flattening text-layer tools (PyMuPDF, LlamaParse) under both judges, **6–31%** by pixel OCR (Tesseract) and **22–27%** by the glyph-preserving grid (LiteParse), versus **85–100%** for vision models.

Unifying law: **the worth of a vision model is proportional to how much of a document's meaning is non-textual** — marginal on a prose page, decisive on a checkbox form or a chart.

### 2.3 No win is self-judged — the ground-truth authors are unranked, and the forms winner authored neither truth
The two frontier vision LLMs each authored one benchmark's ground truth and are ◆-unranked there:

- **Gemini 3.5 Flash** — clean #1 in Finance (89); ◆ ground-truth author scoring ~99 in Insurance.
- **gpt-5** — ◆ ground-truth author (~88) in Finance; clean-ranked #3 in Insurance (80).

The no-self-judging property holds — and the Insurance result *strengthens* it: the corpus's clean #1, **Mistral OCR 4 (92)**, authored *neither* benchmark's ground truth, so its win is graded entirely by rival-family judges against a truth it had no hand in. Gemini's Finance win is likewise judged against gpt-5-authored truth. The frontier tier is vision models plus the vision-OCR parsers; below them the hosted-parser tier is genre-fragile, and the text-dumpers form a structural floor.

### 2.4 Cross-family judges agree on *ranking*, never on *magnitude*
Both corpora: the gpt-5 and Gemini judges agree on vendor order. But the small form corpus sharpened a caveat Finance could not — the **Gemini judge runs +6 to +34 pts more lenient and specifically under-penalizes the two errors that matter most**: it credited garbled OCR as recall (Tesseract scored 85/10 by Gemini vs 30/40 by gpt-5) and missed a wrong binding (a false `portage salarial` tick flagged 5% unsupported by Gemini vs 35% by gpt-5). **Adding Mistral OCR 4 (10th vendor) gave Finance its *own* sharp example of the same blind spot:** Mistral's advanced figure-annotation layer *fabricates* on graphics it can't parse, which the gpt-5 judge prices as **19% unsupported (the highest of any vendor) but Gemini sees only 7%** — the single largest cross-family gap in the Finance set, and exactly the wrong-binding/invented-content error Gemini systematically under-penalizes. **Use the gpt-5 judge for absolute numbers; use the Gemini run only to confirm the order.**

---

## 3. What you can only see by combining (genre-dependence)

- **Vendor rank is genre-dependent at the top, stable at the floor.** LlamaParse is tied-2nd in Finance (86) but **collapses to last in Insurance (31)** — it returned `NO_CONTENT_HERE` on 2 of 3 pages of the watermarked MNH form. Meanwhile PyMuPDF > Tesseract in both corpora (68 > 52; 49 > 44). The frontier moves with genre; the floor order does not.
- **Two distinct failure modes hide behind similar averages.** Text-dumpers *degrade gracefully* (predictable ~−20 binding gap, characters survive). The agentic parser *fails catastrophically* (whole pages → nothing) on layouts it can't handle. For production, a predictable partial failure is often safer than a rare total failure on an unknown subset.
- **Scores are genre-anchored — they do not transfer, and the direction is per-tool, not uniformly harder.** The floor tools drop (68/52 → 49/44) and LlamaParse craters (86 → 31), but **Mistral OCR 4 *rises* 80 → 92 and Pulse 86 → 90** — the clean best on forms (92) exceeds the clean best on finance (89). Forms are all binding and no padding, which punishes flatteners; but vision-OCR tools built for dense text and field grids *improve* there, because the chart-reading strengths that decide the finance ranking become irrelevant. A vendor's "86%" on a finance corpus is meaningless for a forms workload — in either direction.
- **Corpus size decides whether a real change is detectable.** The identical Landing AI DPT-2 upgrade read as **"robust +4.6, every replicate positive"** at 599 pages but **"−3, within ±6 noise"** at n=7 — despite fixing the same defect both times (dense regions dumped as `figure` → real tables + structured `[x]`/`[ ]`). Real model deltas are unmeasurable below ~hundreds of pages.

---

## 4. For enterprises (procurement & deployment)

- **Score on "can I act on this without a human re-checking," not "did it get the characters."** Content recall said PyMuPDF reads the insurance form at 100%; structure-aware said 49% and the output is unusable. The comfortable metric makes you buy the wrong tool. If your POC makes a vendor look great, suspect the POC — the honest metric is *adversarial* to the vendor.
- **Benchmark on your own documents — the headline number does not transfer.** The same tool swings wildly with genre: LlamaParse cratered 86 → 31, while Mistral OCR 4 *rose* 80 → 92. The original 7-page Insurance run cost **~$1.03**; even cumulatively across all five runs (original + DPT-2 + LiteParse + Mistral + Pulse) it is **≈$4.2** plus Landing AI / Pulse credits — still trivially cheap. Run a pilot on 50–100 of *your* pages before signing anything.
- **"$0" is never $0.** A tool that loses bindings shifts cost downstream — every extraction needs a human to re-attach values to fields. And the literal-free tool isn't free either: **PyMuPDF is AGPL/commercial-license** (a legal cost category, not a usage cost; pdfplumber-MIT / pypdf-BSD are the permissive swaps). TCO = API + license + the verification headcount the error rate forces.
- **The boundary is hard: a vision model is mandatory the moment value lives in pixels.** Checkbox state = 0% for the flattening text-layer tools (and ≤31% for any non-vision path); the same is true of chart series, signatures, stamps, and scans. Cheap text-layer extraction is legitimate *only* for born-digital prose-and-table docs that aren't figure- or form-heavy.
- **Buy for your tail, not your average.** Test the weird edge-case documents, not the representative ones — that is where the catastrophic-failure mode (§3) lives.
- **Price ≠ quality at the top.** Gemini 3.1 Flash-Lite (**$1.12**/599 pp) matches Landing AI on figures and is 12× cheaper than gpt-5 (**$13.82**) — and gpt-5 is *not* the figure leader (Gemini Flash 91 vs gpt-5 66 on diagram structure). Segment by the dimension you actually need.

---

## 5. For agent builders (pipeline & correctness)

- **Your extraction layer is a hard ceiling on agent correctness.** If the parser binds a number to the wrong row, no amount of reasoning recovers it — the agent will confidently analyze a wrong-bound value. Extraction is an agent-correctness decision, not "preprocessing."
- **A text-dumper under a document agent isn't RAG, it's a liability.** Flat-text chunks strip the table cells, checkbox state, and chart series the agent needs; it will retrieve the right page and still answer wrong because the value→label binding is gone. Use a structure-preserving extractor and carry the structure *into* the chunks.
- **Route visual facts to the pixels.** If the agent must answer "is box X ticked / what's the Q3 bar value," feed it the rendered page image, not a markdown dump. The efficient design is hybrid: cheap text extraction for prose pages + a vision pass for figure/form pages, routed by page category.
- **The confident silent error is the threat, not the omission.** Even a frontier vision model — gpt-5, clean #3 on the Insurance forms — silently misread a social-security number (NIR) and a date of birth in correct-looking format, and missed a `statut cadre` tick. On PII/financial fields the plausible wrong value is what hurts. Wire deterministic guards for high-stakes fields (SIRET/NIR checksums, date validity, totals that must reconcile) — never let the LLM be the only check on its own output.
- **Dual-model agreement is your cheapest correctness signal.** The cross-validation in §2.3 generalizes: two independent frontier models agreeing is strong signal. For high-stakes extraction, run two different-family models and route disagreements to a human.
- **Match the capability, not just the recall number.** If your agent needs to highlight the source field or support click-to-verify, the specialized parsers all emit **exact bounding boxes** (Landing AI, LlamaParse, Mistral, Pulse, PyMuPDF, LiteParse) — the top-tier coordinate-grade set is Landing AI / LlamaParse / Pulse; vision LLMs give only coarse positions.

---

## 6. Evaluation discipline (shared — the most under-used lesson)

Most of what made these benchmarks *correct* was repeatedly catching their own measurement artifacts. Those meta-lessons transfer to anyone running an internal eval:

- **Never let a model grade its own family.** gpt-5 built the Finance GT (so it is ◆, unranked); Gemini built the Insurance GT (◆, unranked). If you grade Model X's output with Model X, you have measured nothing. Cross-family judging is the minimum bar.
- **LLM judges are lenient on exactly the errors that matter** (§2.4) — they credit garble as recall and miss wrong bindings. Use the stricter judge for magnitudes, cross-family for ranking, and **deterministic validators** for anything checkable. (The project's own POC: a no-LLM binding scorer reproduced the text-dumper collapse on text+tables, but failed on charts — so reserve the LLM judge for genuinely unstructured content.)
- **Know your noise floor before trusting a delta.** Per-item LLM-judge variance is **±20–25 pp**; the same model change was "robust +4.6" at 599 pages and "noise" at 7. A/B-ing a prompt or model change on 10 documents measures noise and calls it a result. Budget enough eval items.

---

## 7. Which vendor is best at what

*Drawn from the Finance element-level eval (6,129 typed elements graded by type), the per-category and figure-judging tables, and the Insurance form/spatial ranking. Read with the ◆ caveat: **gpt-5 is an upper bound in Finance** (it built that ground truth) but **clean-ranked in Insurance**; **Gemini is clean-ranked in Finance** but an upper bound in Insurance. The cross-benchmark structure is what lets each be placed honestly.*

### Best-at-a-glance

| Capability / need | Best pick | Close behind | The evidence |
|---|---|---|---|
| Mixed / unknown documents (pick one) | **Gemini 3.5 Flash** | gpt-5 | no weak element cell; Finance #1 (89) |
| Forms & checkboxes (clean-ranked) | **Mistral OCR 4** | Pulse (Ultra 2) 90 · gpt-5 image 80 (◆ co-authors Gemini ~99 / LA 84, unranked) | clean #1 Insurance (92); checkbox **100%** gpt-5 judge / 97% Gemini; Pulse 94% with the lowest fabrication (4% unsupported) |
| Diagrams / flowcharts / maps | **Gemini 3.5 Flash** | gpt-5 / Landing AI / LlamaParse-agentic | diagram structure 91–92 vs pure text-layer ~45–50 |
| Charts (data fidelity) | **Gemini 3.5 Flash** | gpt-5 | element-level charts 90; figure graph-data 85 |
| Tables (structure) | **Gemini 3.5 Flash / LlamaParse** | Landing AI / PyMuPDF | tables 97 (both); LA & PyMuPDF 93 |
| KPIs / financial numbers | **Gemini Flash / PyMuPDF / gpt-5** | Landing AI | KPI 100 (three-way tie); LA 98 |
| Scanned / image-based pages | **Landing AI** (or any vision model) | gpt-5 / Gemini | best Image/Photo category (88); text-layer tools ~0 |
| Exact source coordinates / provenance | **Landing AI / LlamaParse-agentic / Pulse** | Mistral · PyMuPDF · LiteParse (boxes too, lower tiers) | every specialized parser emits exact element boxes; vision LLMs emit coarse positions only |
| Lowest hallucination / never invents | **PyMuPDF / Pulse (Ultra 2)** | Gemini Flash / Flash-Lite | 5% unsupported (tied lowest of all — but **Pulse is the cleanest *vision* reader**: 5% *with* full figure/table capture, vs the worst, Mistral OCR 4 at 19% — its figure annotation fabricates) |
| Best value for money | **Gemini 3.1 Flash-Lite** | — | $1.12 / 599 pp; matches Landing AI on figures, 12× cheaper than gpt-5 |
| Cheapest born-digital tables (budget 0) | **PyMuPDF** (note AGPL → pdfplumber/pypdf) | Tesseract | tables 93 / KPI 100, never invents — but dies on forms/figures |
| Free prose-only OCR | **Tesseract** | — | prose 96 — but never trust its numbers (tables 69, charts 41) |

### Per-vendor verdicts (across both genres)

- **Gemini 3.5 Flash — the cross-genre champion and the safe default.** The only vendor with *no weak element type*: tables 97, charts 90, diagrams **92**, KPI 100, prose/titles 100, chrome 91. Finance clean #1 (89) and the figure-dimension leader (diagram structure 91 — above gpt-5's own 66 in a blind judge). In Insurance it co-authored the ground truth (◆, ~99) and confirmed 15/15 checkboxes at high res. At **$7.12** it's roughly half gpt-5's cost. One small robustness scar: a single degenerate page (Alpha p5) hit the 16k output cap via runaway repetition (1/599). If you deploy one parser for unknown documents, this is it.
- **gpt-5 (image / file) — a strong forms vision reader, no longer the champion; elsewhere a benchmark yardstick.** Clean #3 in Insurance (80, checkbox 85%, 11% unsupported) — it held the forms crown until the Mistral (92) and Pulse (90) runs displaced it. In Finance it built the ground truth, so its ~88 is an upper bound, not a ranking. Most expensive (**$12.54–$13.82**) and coarse coordinates only. Its signature failure mode is the **confident silent error**: it misread a NIR and a date of birth on the insurance form in correct-looking format, and missed a `statut cadre` tick — under-capture and the occasional wrong value, not wrong bindings. Use it as a second-family verifier rather than the primary forms extractor, and guard its PII fields.
- **Gemini 3.1 Flash-Lite — the value pick.** Gemini Flash's shape minus a few points on the hard visuals (charts 86, diagrams 87) for **$1.12** — 12× cheaper than gpt-5 and level with Landing AI on the figure dimensions. The right default when cost dominates and documents aren't diagram-critical. (Flash-Lite was not run on Insurance — the clean vision-tier vendors tested there are Mistral, Pulse and gpt-5 — so it has no forms number; infer from its Finance proximity to Flash.)
- **Landing AI (DPT-2) — the provenance/coordinates option, strong all-rounder.** Finance 86 with the **best Image/Photo category (88)**, diagrams 89, and — uniquely among the high-recall tier — **exact bounding boxes**. In Insurance (◆ co-author) DPT-2 reads checkboxes at 94% and *corrected the false tick* the legacy model asserted. Trade-offs: highest padding among the leaders (11% unsupported), and it's the vendor whose two standalone element evals are still on the legacy endpoint (a known follow-up; treat its element-level numbers as a floor). Pick it when you need exact source coordinates *and* figure reading.
- **LlamaParse (agentic) — top born-digital all-rounder with real tail risk.** On born-digital docs it ties the top: tables **97**, prose/titles 100, and — unlike the other parsers — it *reads figures* (charts 83, diagrams 83), plus exact boxes and low padding (10%). But it has a **cliff**: in Insurance it collapsed to last (31), returning `NO_CONTENT_HERE` on 2 of 3 watermarked form pages. Two operational rules: (1) you **must** use the `agentic` tier — `accurate` silently drops whole pages; (2) keep it away from forms and unusual layouts. The figure-*dimension* judge under-counts its diagrams (30) because it emits them as inline prose; the element-level 83 is the fair number.
- **Mistral OCR 4 (advanced config) — the cheap figure reader that fabricates on finance, and the clean #1 on forms.** Run at its most capable tier (`mistral-ocr-4-0` + the Document-AI per-image annotation that *describes* charts), it enters the vision tier at **80%** (6th among real vendors, just below the four-vendor 86 tier), preserves structure (gap −4, unlike the text-layer tools), is near-top on text (96, behind Pulse's 97) and is 2nd-best on image/photo (86, behind Landing AI's 88), and genuinely reads charts (chart-data 59 vs text-layer ~12–29 — a structure-aware confirmation that OCR 4 *can* approach the agentic parsers on figures) at **~$3/599pp**. But it is **the only vendor whose dominant error mode is fabrication**: the highest unsupported of any vendor (**19% gpt-5; 7% Gemini**), because the annotation layer *invents* content on graphics it can't parse (on a page of certification logos it produced a non-existent flowchart and a Portuguese document-management UI). Adopt for text/tables and cheap chart reach, but surface its confidence scores and gate figure-derived claims behind verification. **On the Insurance forms (run 2026-06-23) the same tool flips to clean #1: 92% structure-aware, 8% unsupported, checkbox 100% (gpt-5 judge) / 97% (Gemini)** — forms have no charts to invent on, and they reward exactly its dense-OCR and checkbox-glyph strengths. That 6th-with-fabrication → clean-#1 flip is the sharpest "genre picks the tool" evidence in the two-benchmark set.
- **Pulse (Ultra 2, advanced config) — the cleanest vision reader; the steady inverse of Mistral.** Run at its most capable tier (`pulse-ultra-2` + `refine` + figure description), it joins the **86%** Finance high-quality cluster — **top of the field on text (97) and tables (90)**, ties best on Mixed (93), and reads charts at **Chart-73** (above Mistral's 62) by writing chart data *inline into the page markdown* rather than a figure channel (so it was scored by the headline fair total, not the structured figure judge — which it was excluded from to avoid a misleading ≈0 on its empty `[Image]` placeholders). Its signature is **fidelity**: **5.8% unsupported (gpt-5), 1.5% (Gemini)** — the lowest of any vision vendor, furthest into the "safe & accurate" corner. The exact inverse of Mistral: same hosted-document-AI class, opposite end of the trust axis. Consistent across genres — clean **#2 on the Insurance forms (90%, 4% unsupported)** too. Its cost is **latency** (`refine` ~19 s/pg median, ~3.6× Mistral) and credit-based billing (~10 cr/pg). Adopt where a confidently-wrong figure is the dominant risk and throughput is not the binding constraint. See [`PULSE_ADD.md`](PULSE_ADD.md).
- **PyMuPDF — the spiky born-digital text-layer specialist.** Elite where values live in a born-digital text layer: tables **93**, KPI **100**, prose 97, and even charts **83** (it lifts data labels verbatim) — and it *never invents* (5% unsupported, lowest of all). But it **collapses on anything purely visual**: diagrams 50, chrome 65, ~0 on scanned pages, and it is **disqualified for forms** (Insurance 49, checkbox 0%, structure gap −23). Note the license: PyMuPDF is **AGPL-3.0 / paid-commercial**, not free for proprietary use — use pdfplumber (MIT) / pypdf (BSD) at the same tier. A cheap, honest first pass for born-digital, non-form, non-diagram documents — nothing more.
- **Tesseract — the prose-only OCR floor.** Fine on rendered body text (prose 96, titles 92) and truly free (Apache-2.0), but weak and *error-prone* on everything structured: tables 69 with the lowest fidelity (emits wrong numbers), charts 41, diagrams 45, checkbox 6–31%. Last in Finance; second-last on the forms (44 — only LlamaParse's cliff to 31 sits below it). Reach for it only when budget is zero and you need prose — and never trust its numbers.

---

## 8. The combined decision rule

**PDF extraction is a router problem, not a vendor-selection problem.** The benchmarks make this structural, not stylistic: no single tool sits on the cost-quality Pareto frontier — Gemini Flash wins mixed pages and diagrams, Mistral OCR 4 wins forms (yet fabricates on charts), PyMuPDF is unbeatable-for-$0 on born-digital tables, Landing AI owns scanned pages and exact coordinates, LlamaParse leads born-digital all-round but cliffs to last on a watermarked form — and the same tool swings 86→31 (or 80→92, the other direction) with genre, so "which parser is best" presumes a single objective over a homogeneous input that does not exist. Real document streams are heterogeneous *within a single file*: one annual report carries prose, gridded tables, charts, diagrams, and the occasional scanned insert, and the optimal extractor changes page to page. That makes the unit of decision the **page (or region), not the document or the corpus** — and the signal you route on is both cheap and already present: the page category (Text / Table / Chart / Form / Scanned) is the dominant predictor of which tool wins and is detectable with a fast classifier or a cheap model's first pass. A router also converts each tool's known blind spot into a *constraint* instead of a silent error (never send a checkbox page to a text-dumper, never send a watermarked form to the agentic parser, never trust Tesseract's numbers) and lets you concentrate the $13.82-tier spend on the handful of figure/form/scanned pages that earn it while the bulk of easy prose flows through a $0–$1.12 path. The cost is real — a classification step, several integrations, and a router that can itself misroute — but the per-genre spread the benchmarks measure (40–47 pp on the separating genre; 92→31 across ranked vendors on forms) dwarfs it. The two routing axes are therefore **(input category → extractor)** and **(downstream stakes → verification depth)**: the table below is the first axis written out; §5–6 are the second.

```
                          PDF page  (the unit of routing)
                                  |
                                  v
                   +------------------------------+
                   |   Classify page category     |  <- cheap classifier
                   +------------------------------+     or cheap first pass
                                  |
   ===== AXIS 1 : page category --> extractor ==========================================

   Form / checkbox / signature   -->  VISION REQUIRED  ·  Mistral OCR 4 (Pulse = low-fabrication alt)
   Scanned / image-based         -->  Vision  ·  Landing AI · gpt-5 · Gemini
   Chart / diagram-heavy         -->  Gemini 3.5 Flash   (or gpt-5 · Landing AI · LlamaParse-agentic)
   Born-digital tables / numbers -->  PyMuPDF $0 (AGPL -> pdfplumber/pypdf)  ·  or Flash-Lite $1.12
   Plain prose                   -->  Cheap tier  ·  Tesseract · PyMuPDF · Flash-Lite
   Mixed / unknown               -->  Gemini 3.5 Flash   (safe default)

   override: need exact coordinates / provenance?  -->  Landing AI · LlamaParse-agentic · Pulse

                                  |   (all routes converge)
                                  v
                          +-----------------+
                          | Extracted output|
                          +-----------------+
                                  |
                                  v
   ===== AXIS 2 : downstream stakes --> verification depth =============================

                          +-----------------+
                          | Stakes?         |
                          +-----------------+
                            |             |
              High (PII / money)         Low
                            v             v
   Dual-family models + deterministic    Single pass -- ship
   validators (checksums · totals ·
   ranges)  ->  human on disagreement
```

*Axis 1 (page category → extractor) is the branch set; Axis 2 (stakes → verification depth) is the tail. **Override:** if you need exact source coordinates or click-to-verify provenance, route to Landing AI, LlamaParse-agentic or Pulse regardless of category. The economics: the premium vision spend is reserved for the few form/figure/scanned pages that earn it, while the bulk of prose flows through the $0–$1.12 path. The table below is the same policy as a lookup.*

| If your documents are… | Use | Why |
|---|---|---|
| Forms / checkboxes / signatures / stamps | **A vision-tier tool** (Mistral OCR 4; Pulse if fabrication risk dominates) — not optional | checkbox state = 0% for flattening text-layer tools; Mistral 92 / checkbox 100%, Pulse 90 / 4% unsupported |
| Scanned / image-based pages | **Vision model** | text-layer tools return nothing where there is no text layer |
| Chart- / diagram-heavy (M&A, IR decks) | **Gemini 3.5 Flash** (or gpt-5 / Landing AI / LlamaParse-agentic) | figure-reading tier 83–92; pure text-layer ~45–50 |
| Born-digital, table/number-heavy, budget = 0 | **PyMuPDF** ok (note AGPL → pdfplumber/pypdf) | tables 93 / KPI 100 element-level, never invents — but dies on forms/figures |
| Mixed / unknown corpus | **Gemini 3.5 Flash** | no weak element type; safe cross-genre default |
| Need exact source coordinates / click-to-verify | **Landing AI**, **LlamaParse (agentic)** or **Pulse** | the high-quality tier that emits exact boxes (all specialized parsers do; these three at top quality) |
| High-stakes fields (PII, money) — any genre | **Two different-family models + deterministic validators** | guards against the confident silent error |

---

## 9. Honest limits

- **Insurance is n = 7.** It corroborates Finance *qualitatively* — replicating the structure-gap thesis, extending it to a new genre, and exposing LlamaParse's cliff — but its absolute numbers carry ±20–25 pp per-page noise and must not be pooled with, or weighed equally against, the 599-page corpus.
- **Absolute magnitudes are gpt-5-judge-specific** in both corpora; the cross-family spread is the real uncertainty band.
- **Both corpora are born-digital** (the only scanned/image pages are the few inside the IAR annual report). Neither establishes performance on a true scanned-document corpus.
- **The ◆ ground-truth authors (gpt-5 in Finance, Gemini in Insurance) are upper bounds, not rankings** — read them for context only.

---

### Sources
- Finance: [`results/FAIR_TOTAL.md`](results/FAIR_TOTAL.md), [`results/BY_DOCUMENT.md`](results/BY_DOCUMENT.md), [`results/WHO_IS_GOOD_AT_WHAT.md`](results/WHO_IS_GOOD_AT_WHAT.md), [`results/EXTRACTION_COMPARISON.md`](results/EXTRACTION_COMPARISON.md), [`FINAL_REPORT.md`](FINAL_REPORT.md), [`LANDINGAI_DPT2_REBENCH.md`](LANDINGAI_DPT2_REBENCH.md).
- Insurance (sibling repo `../PDF parsing test - Insurance`): `results/FAIR_TOTAL.md`, `results/SPATIAL_RANKING.md`, `FINDINGS.md`.
