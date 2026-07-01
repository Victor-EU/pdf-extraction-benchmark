# Is Document AI Replacing Traditional OCR? — a working thesis

*A strategic read, 2026-06-30, grounded in the two structure-aware benchmarks in this repo
(599 pages of finance/business documents in [`FINAL_REPORT.md`](FINAL_REPORT.md) + a sibling
French insurance-forms corpus; cross-benchmark synthesis in [`CIO_TAKEAWAY.md`](CIO_TAKEAWAY.md)).
This is the **extrapolation** layer, not the leaderboard — informed opinion built on measured data.
Weight it accordingly: every number cited is from our own runs; every forward claim is judgment.*

---

## TL;DR

Yes, directionally — but "replace" is the wrong mental model. **OCR isn't being eliminated; it's
being demoted to a substrate, while the product moves up the stack from "recover the characters" to
"recover the structured meaning, with bindings intact."** The disruptor underneath is the
vision-language model (VLM), which is why charts and complex layouts finally cracked. But the category
is being squeezed from *above* at the same time — general multimodal models (Gemini, GPT-5) match or
beat the specialised parsers at *reading* — so the durable moat for a "Document AI" product is **not**
the reading; it's the engineering shell around it: exact coordinates, calibrated confidence,
determinism, robustness, and deployment. And the one thing gating whether the replacement actually
completes is **fabrication**: VLM extractors fail by confidently *inventing* content, where OCR failed
by visibly *garbling* it. The winners will be whoever pairs VLM-grade understanding with OCR-grade
trustworthiness.

---

## 0. First, clear up a common confusion: coordinates are table stakes, not a differentiator

A frequent mistake when comparing these tools is to treat **bounding-box coordinates** as a premium
feature of one vendor. They aren't. In our capability matrix, *every* document-AI parser emits exact
element boxes — Landing AI, LlamaParse, Mistral, Pulse, even PyMuPDF and LiteParse. The line that
"emits exact boxes" actually draws is **the parser class vs. the raw-LLM class**:

| Class | Coordinates |
|---|---|
| Document-AI parsers (Landing AI, LlamaParse, Mistral, **Pulse**, PyMuPDF, LiteParse) | **exact element boxes** |
| Native-vision LLMs (Gemini Flash/Lite, GPT-5) | coarse positions only |
| Traditional OCR (Tesseract) | word boxes (no structure) |

So coordinates don't make Pulse better than LlamaParse — they both have them. What separates two
parsers in the *same* class is **fidelity and robustness**, not whether boxes exist. (Concretely:
Pulse fabricates less than LlamaParse — 5.8% vs 10.2% unsupported on finance — and degrades
gracefully where LlamaParse falls off a cliff: on the insurance forms LlamaParse collapsed to last
place, returning `NO_CONTENT_HERE` on watermarked pages, while Pulse stayed clean #2.) **Compare tools
*within* a class on trust and robustness; compare *across* classes on coordinates + structure.**

---

## 1. The shift: OCR isn't eliminated, it's subsumed — the product moved up the stack

Traditional OCR sells one output shape: a **flat character stream** (plus, maybe, word boxes). Modern
Document AI sells a different shape entirely: **structured, bound data** — tables as grids, fields as
key-value pairs, checkboxes as *state*, figures as descriptions, all carrying coordinates and
confidence.

OCR didn't disappear from this; it got *wrapped*. Pulse's `refine` pass **is** OCR. These engines
still recognise characters — they just bury that step inside layout analysis, structure recovery, and
semantics. The character-recognition problem became a *component*, not the product.

This is the entire thesis of our benchmark restated as a market trend. We measure not "are the
characters present" but "**is each value still bound to the right place**" — the right row/column/series
in finance, the right field and checkbox state on forms. Tesseract (pure OCR) finished **dead last on
the finance corpus** (52% structure-aware) and second-last on forms (44% — above only LlamaParse's
watermark collapse to 31%), reading checkbox *state* at just 6–31% depending on judge (the outright 0%
on checkboxes belongs to the text-layer *flattening* tools, PyMuPDF and LlamaParse), precisely because
it's still selling the old output shape. The market is migrating from *transcription* to *bound
meaning*, and the tools that only transcribe are being left behind for anything structured.

---

## 2. The disruptor underneath: the VLM — which is why charts finally cracked

The discontinuity is the vision-language model. It's worth being precise about generations, because
"Document AI" has meant three different things in five years:

- **Gen 0 — Traditional OCR** (Tesseract, classic ABBYY/Textract OCR): pixels → characters. No
  structure, no semantics.
- **Gen 1 — Classic Document AI** (early Azure Document Intelligence, AWS Textract, Google Document AI):
  CNN layout analysis + OCR + rules/templates. Good on *fixed forms*, weak on figures and unusual
  layouts.
- **Gen 2 — VLM Document AI** (Pulse Ultra, Mistral OCR 4, Landing AI DPT-2, LlamaParse agentic):
  vision-language-model-backed. **Reads charts and diagrams** — the thing no prior generation could do.

That last leap is the one that feels like a platform shift rather than an increment, and our data
shows it cleanly: **graph-data fidelity is 59–85 for the VLM tier vs 12–29 for everything OCR/text-layer
based.** Reading a label-free bar chart and recovering its *values* is a genuinely new capability, and
it's VLM-native. This is what makes "Document AI is replacing OCR" feel true — Gen 2 can do things Gen 0
structurally cannot.

---

## 3. But the category is squeezed from *above* — which reveals where the real moat is

Here's the finding that reframes everything. On our finance corpus, the top capture score didn't go to
a specialised document-AI product. It went to **Gemini Flash — a general multimodal LLM — at 89%,
ahead of the specialised-parser cluster at 86%** (Mistral, at 80, sits below that cluster).

So *reading the document* is **not** the document-AI products' durable advantage. General frontier
models match or beat them, and they get cheaper and better every quarter. What the specialised parsers
have that a bare Gemini call does not is the **engineering shell**:

- exact element **coordinates** (Gemini emits only coarse positions),
- per-field **calibrated confidence** (the input to a straight-through-processing decision),
- **determinism** and reproducibility,
- page-level **robustness** and whole-document async handling (1,000-page files, retries),
- **in-tenant / VPC deployment** for compliance.

That shell is the moat that survives. The reading is commoditising toward "whatever the best multimodal
model is this month"; the **provenance-and-trust layer is the defensible product.** This is also why
our benchmark's most durable operational lesson is *"the model is swappable; the pipeline is the
asset"* — build the routing, validation, reconciliation, and review layer, and keep the extractor
behind an interface you can swap in a config change.

---

## 4. The gating problem: fabrication — and why it decides whether "replace" completes

This is the asymmetry that could *stall* the replacement, and it's the sharpest finding in our whole
benchmark:

- **Traditional OCR fails by omission/garbling** — visibly wrong, catchable, auditable. You can *see*
  that a character didn't resolve.
- **VLM Document AI fails by confident invention** — it produces fluent, plausible, *wrong* content.
  Mistral OCR 4, on a page of certification logos, hallucinated a generic "Start → Process → End"
  flowchart and a fake Portuguese document-management UI (19% of its output unsupported — the highest
  of any tool we tested). Nothing announces this; it flows straight into the downstream system.

For high-stakes pipelines — claims, underwriting, financial statements, anything where a confidently
wrong number is catastrophic — **a plausibly-fabricating extractor is disqualifying no matter how high
its average accuracy**, because you cannot tell the invented value from the real one. This is the real
barrier to "Document AI replaces OCR": OCR's *one* enduring virtue is that it doesn't make things up.

So the replacement only completes for the tools that acquire OCR-grade trustworthiness *while keeping*
VLM-grade understanding. That frontier is exactly where the most interesting Gen-2 tools sit:
**Pulse, for instance, is the lowest-fabrication VLM extractor we measured (5% unsupported) while still
reading structure and figures and emitting coordinates.** It's unremarkable on the raw capture
leaderboard, but it's a data point on the *only axis that gates the replacement* — "can a VLM extractor
be trusted the way OCR was?" The vendors who win this market will be the ones that move *down* the
fabrication axis without giving up the understanding, and/or that surface confidence honestly enough
that a validation layer can gate the uncertain cases.

> **The cross-vendor corollary (don't skip this):** "Document AI" is not one fidelity profile. Two
> hosted engines — Mistral and Pulse — run at the *same* advanced-tier config landed at **opposite ends
> of the trust axis (19% vs 5% fabrication).** "It's a Document-AI product" tells you nothing about
> whether it invents. **You must measure fabrication per vendor, per document type, on your own data.**

---

## 5. Where traditional OCR survives anyway (the limits of "replace")

"Replace" overstates it. OCR keeps three defensible footholds:

1. **Economics at scale.** OCR is ~free and instant; VLM Document AI is per-page paid and *slow*
   (Pulse is ~19 s/page; Tesseract is ~1 s/page and $0). For billion-page archival digitisation where
   you just need a searchable text index, OCR wins by orders of magnitude. Document AI earns its price
   only where *structure and figures* carry the value.
2. **Born-digital text.** If the PDF already has a clean embedded text layer, you need *neither* OCR
   nor Document AI for the text — a $0 library (PyMuPDF / pdfplumber) lifts it perfectly. Document AI's
   real territory is **scans, forms, tables, and figures** — not "all PDFs."
3. **Fixed high-volume forms.** Template / positional extraction still beats a VLM on a *known* layout
   (e.g. a specific ACORD form) — cheaper, deterministic, and highly reliable on known fields (an
   industry/vendor-claimed profile; we did not benchmark template extraction ourselves). The VLM's
   advantage is the *non-standard long tail*, not the standardised core.

---

## 6. What this means for us

- **Don't shop for "the best extractor." Build the pipeline.** `classify → route → extract → validate
  → review`, with the extractor behind a swappable interface. The leader churns; the pipeline is the
  asset. (Same conclusion two independent benchmarks reached — see [`CIO_TAKEAWAY.md`](CIO_TAKEAWAY.md).)
- **Route by document type, not by brand.** Born-digital text → a $0 text-layer library. Fixed forms →
  template extraction. Scans/figures/long-tail → a VLM Document-AI parser. Charts/understanding → a
  general multimodal LLM. No single tool wins all four cells.
- **Treat coordinates + confidence + determinism as the procurement criteria for the parser tier** —
  not raw capture, where the cheap general LLMs already match the specialists.
- **Make fabrication a first-class, measured metric.** Build a small golden set per high-volume
  document type and score *unsupported/invented output*, not just recall. Gate material fields (PII,
  money, elections) on confidence regardless of which vendor leads.
- **Expect convergence.** Today the ideal bundle — VLM understanding + coordinates + calibrated
  confidence + cheap/fast — is *split* across tools (general LLMs have understanding + cheap; parsers
  have coordinates + determinism; nobody has all four). Whoever closes that gap wins the "intelligent
  document processing" market that rules-plus-OCR used to own. Watch the fabrication-vs-understanding
  frontier; that's where the race is.

---

### One-line version for the deck

> Document AI isn't *replacing* OCR — it's **subsuming** it and moving the product from "characters" to
> "structured meaning," powered by VLMs that finally read figures; the durable moat is coordinates +
> confidence + determinism (not the reading, which general LLMs already match), and the race is won by
> whoever pairs VLM understanding with OCR-grade trustworthiness.

---

## Appendix — Build or Buy? Should you build a custom extraction/governance layer?

The thesis says the durable value is the **governance shell** — coordinates, confidence,
reconciliation, fabrication-gating, routing, validation — not the reading. The natural follow-on for
an engineering team is: *so should we build that shell, or buy it?* Here is the decision framework.

### The layer you'd build is the right one — if you build the right layer

Building the orchestration/governance layer (rather than an extraction engine) is building the part
the market isn't eating. Three reasons it ages well:

1. **Model progress is a tailwind, not a threat.** If the extractor sits behind a vendor-blind slot,
   every time the frontier improves your commodity *input* upgrades for free while your moat is
   untouched. A team that builds an *extraction engine* gets obsoleted by the next model; a team that
   builds a *vendor-blind governance layer* gets fed by it. That inversion is the single best reason
   this kind of project still makes sense to start in 2026.
2. **It targets the gate — fabrication.** The durable move is to turn invented/unverifiable values
   into a first-class defect (flag them, withhold them, route them to review) instead of trusting an
   uncalibrated vendor "confidence" score. Vendor confidence is not the same as ground truth; a layer
   that *grounds* trust rather than *claims* it is doing the hard, non-commoditizing thing.
3. **It's the part a single-vendor platform structurally won't give you** — cross-vendor neutrality
   and cross-source reconciliation (fusing a model's read against the document's own exact text/geometry).
   No vendor will build the layer whose whole job is to keep them swappable.

### But ask the three questions that actually decide it

**1. Your competitor is a governance *platform*, not a naked model.** Beating "send everything to one
LLM" is the easy win — you'll get it. The comparison a buyer actually makes is against Reducto, Extend,
Landing AI ADE, Azure Document Intelligence, LlamaCloud, Unstructured — which *already* emit boxes +
grounding + validation + human-review. Against **those**, the build case narrows to three things:
**cross-vendor neutrality** (every platform is a walled garden), **no-egress / residency** (the on-prem,
data-can't-leave case), and **cross-source glyph-level reconciliation** (substituting the exact printed
character for the model's transcription and binding a coordinate to it — vendor-independent, and not
something single-vendor platforms do). Benchmark yourself against a platform that emits boxes, not
against a naked model — that's the honest test.

**2. Separate durable value from depreciating value — and lead with the durable one.**
- **Audit / trust / compliance = durable.** A universal model scores *zero* on it by construction, and
  no amount of model progress erodes it. This is the part that compounds.
- **Cost optimization ("keep the easy pages local, don't pay to send them to vision") = depreciating.**
  It's a real lever today, but it shrinks every time frontier vision gets cheaper — and that's the one
  thing you can bet on. A design *sold on cost* in 2026 looks weak in 2028; a design *sold on
  governance* doesn't. Treat the cost savings as a bonus that erodes; put the value story, and the moat
  investment, on the audit/compliance axis.

**3. Is it your product, or a feature?** If extraction governance is the thing you *sell or license*,
the build-vs-buy logic inverts: you build your differentiator, full stop — you don't buy the thing you
ship. If extraction is a *feature* of some other product, building the full classify→route→reconcile→
verify→flywheel pipeline is over-engineering; buy a platform and spend the team elsewhere.

### The risks to budget for

- **Maintenance surface vs. team size.** A multi-stage pipeline is a lot to keep alive as vendors churn
  output formats and inherited priors go stale. Stay **thin** where vendors are racing (extraction
  smarts, table structure, chart reading — they'll out-run you); stay **thick** only where they
  structurally won't go (cross-vendor reconciliation, residency, the correction flywheel).
- **The differentiated core is also the fragile core.** Cross-source reconciliation (glyph substitution
  + coordinate binding) is your most copy-resistant mechanism *and* your most brittle one (garbled text
  layers, vision-paraphrased prose, region-segmentation cascades). Concentrate engineering there, not
  on shaving another cent off the routing.
- **The flywheel is the real moat — and it needs volume.** A correction-feedback loop with no
  throughput is just a feature; it only compounds into a defensible advantage above some document
  volume, where your proprietary corrections tighten the system faster than a competitor can. Below
  that, you have a clever architecture with no compounding edge.

### Bottom line

**Build it — if it's the product, and if you sell it on audit/compliance/cross-vendor-neutrality, not
on cost.** You'd be building on the one layer model progress *feeds* instead of *eats*, and solving the
fabrication gate the whole market is stuck on. Two adjustments to get right: (1) re-aim the value story
and the eval from *"we beat the naked model on cost"* to *"we beat a governance platform on neutrality
+ residency + provenance, and we make fabrication impossible to ship silently"* — that's the real claim
and the real buyer comparison; (2) treat cost-routing as a depreciating bonus and pour the moat budget
into reconciliation robustness and flywheel throughput. **Grounded, cross-vendor, replayable trust is
the thing that doesn't commoditize — but you have to sell it, and defend it, on that axis.**

---

*Evidence base: [`FINAL_REPORT.md`](FINAL_REPORT.md) (finance, 599 pp, 11 tools, structure-aware),
the insurance-forms sibling benchmark, [`PULSE_ADD.md`](PULSE_ADD.md) /
[`MISTRAL_ADD.md`](MISTRAL_ADD.md) (the two hosted Document-AI engines at opposite ends of the trust
axis), and [`ENTERPRISE_EXTRACTION_PLAYBOOK.md`](ENTERPRISE_EXTRACTION_PLAYBOOK.md). Forward-looking
claims are judgment, not measurement — validate against your own document mix before betting budget.*
