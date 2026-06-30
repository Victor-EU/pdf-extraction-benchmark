# Running an Insurance Company's Document-Ingestion Stack — an Operating Playbook

*Strategic companion to [`ENTERPRISE_RECOMMENDATION.md`](ENTERPRISE_RECOMMENDATION.md) and the
benchmark in [`FINDINGS.md`](FINDINGS.md). The benchmark is a 7-page born-digital probe; a real
insurance stack is a different beast. This file extends the findings to production and is explicit
about what is **measured** vs **industry reasoning** (see the last section).*

## The one-line bet

**Bet on the pipeline and the data flywheel, not on a model.** Your durable assets are document-type
routing, a validation/business-rules layer, human-review tooling, provenance/audit, and the
correction-feedback loop. The extraction model is the *least* durable decision — this corpus says
Mistral OCR 4 then gpt-5; the sibling finance corpus put **that same Mistral 5th-of-10 and said
Gemini**; in six months it will say something else, and a silent config bug in this very repo was
mis-scoring a vendor (legacy Landing AI endpoint) until it was caught. One tool topping this benchmark
while trailing the finance one is the flip in hand. Architect so swapping the model is a config change,
not a rebuild.

---

## 1. Map the mix before choosing any tool (step zero)

The right approach differs entirely per cell of **document type × input quality × business
criticality × volume**:

- **Standardized forms** — ACORD 25 (COIs), 125/126/140 (commercial apps), dec pages: high volume,
  positionally stable.
- **Semi-structured** — FNOL, claim forms, loss runs, supplemental questionnaires.
- **Unstructured** — adjuster narratives, medical records, police reports, correspondence, email.
- **Input quality** — born-digital → clean scan → fax → phone photo → **handwriting**. The benchmark
  tested *only* born-digital; in production, input quality drives accuracy far more than model choice.
  A faxed, handwritten FNOL is the hard case, not the model leaderboard.

Most value sits in a handful of high-volume types. Instrument volume by type × quality × criticality
first, and spend there.

## 2. Exploit standardization ruthlessly (the biggest lever the benchmark doesn't see)

For ACORD and other standardized layouts, **template / positional extraction (or a doc-AI model with
a fixed schema) beats a frontier LLM** — deterministic, cheap, auditable, ~99% on known fields. Don't
pay vision-LLM latency to re-derive a known grid. Reserve expensive AI for the non-standard long tail.
**Classification** ("which ACORD / which carrier's form / freeform") is the highest-ROI model you build.

## 3. The architecture is `classify → route → extract → validate → review`

The model sits behind a stable interface; everything valuable is around it. (Detailed diagram in
`ENTERPRISE_RECOMMENDATION.md`.)

## 4. Vision is required for the form/selection layer — prefer doc-AI over raw LLMs in production

The benchmark's core finding, and it generalizes: **checkbox/selection state, signatures, stamps, and
layout bindings are near-invisible to the text layer** — the flattening text-layer parsers (PyMuPDF,
LlamaParse) scored **0% on checkbox state** under both judges, OCR barely better (Tesseract 6–31%),
and even the best-structured text-layer tool (LiteParse, whose grid keeps the literal `[X]` glyph)
only 22–27% and noisily, vs 85–100% for vision; only vision recovers it reliably. For production, lean on **doc-AI engines** (Azure
Document Intelligence, AWS Textract, Google Doc AI, Landing AI ADE/DPT-2, Pulse/runpulse.com) for the structured layer
rather than a bare LLM: they emit **geometry + per-field confidence + determinism**, and confidence is
what powers your straight-through-processing decision. Use vision **LLMs** for the messy long tail and
for understanding tasks (classify, summarize, semantic QA over medical narratives).

## 5. Validation is where you win — design it to catch *confident silent errors*

The benchmark's sharpest warning: a top vendor (gpt-5) misread a NIR and a date of birth, and the
clean #1 (Mistral OCR 4) fabricates content on low-signal pages — fluent, confident, wrong, on PII
fields. No model self-reports that. You catch it with structure:

- **Checksums / format rules** — SSN/NIR, VIN, policy-number formats, NAIC codes, dates.
- **Cross-field logic** — loss date within policy period; amounts foot; limits ≥ claimed.
- **Cross-system reconciliation** — does this policy number exist in the admin system? does the insured
  name/address match? (Catches most extraction errors essentially for free.)
- **Ensemble the critical / fraud-relevant fields** — claim amount, payee bank details, policy number,
  dates — with two independent methods and flag disagreement. Payee-detail tampering is a fraud vector.

A wrong value flowing silently into a claim payment is the dominant risk; a flagged gap is benign. Tune
the whole layer around that asymmetry.

## 6. Run on confidence-gated STP + a human-review flywheel

The business KPI is **straight-through-processing rate at an accepted accuracy bar**. Auto-accept
high-confidence; route the uncertain / high-stakes minority to humans. Capture every human correction —
that labeled data is the **moat**: it tunes templates, thresholds, and eventually fine-tunes. Measure
**field-level accuracy, confidence calibration, and review cost** — not a structure-recall percentage.

## 7. Make compliance/security a first-class constraint

Insurance is PII- and (health / disability / workers-comp lines) **PHI/HIPAA**-heavy. Data residency or
contractual terms may *forbid* sending documents to a public frontier API at all — which can decide the
architecture toward **VPC / on-prem doc-AI** regardless of leaderboard accuracy. You also need
click-to-source provenance (audit trails), retention/deletion, and access control. (The benchmark repo
gitignoring its own corpus as identifying data is the small version of this.)

## 8. Continuously evaluate on *your* documents

Build golden sets per high-volume doc type from real traffic; measure field accuracy + calibration +
STP; re-run on every model/version change. The benchmark is the cautionary tale: a legacy-endpoint
config bug silently understated a vendor, and a model version bump (DPT-2) changed behavior and fixed a
real error. Your eval harness is permanent infrastructure.

## Build vs buy

Buy the commodity OCR / doc-AI layer; **build the insurance-specific routing, validation rules,
reconciliation, and review tooling.** That's where defensible IP and accuracy live — not in
re-implementing OCR.

---

## What is benchmark-grounded vs. extrapolation

Weight these differently.

- **Grounded** (n = 7 French born-digital forms, two judge families — see `FINDINGS.md`): vision is
  required for the form/checkbox layer; text-layer extraction is disqualified for forms despite perfect
  raw-content recall; confident silent errors on PII happen even to the best model; model choice is not
  durable.
- **Extrapolation** (industry reasoning, *not* measured here): the ACORD/standardization lever;
  scanned/fax/handwriting/photo input quality; STP economics; compliance forcing on-prem; build-vs-buy.
  Validate these against **your** mix before committing budget — as `ENTERPRISE_RECOMMENDATION.md`'s
  "Scope & limits" warns.

## First moves (sequencing)

1. Instrument current volume by doc-type × input-quality × criticality.
2. Stand up classification + an eval harness on your top 3–5 types.
3. Template-extract the standardized high-volume forms (fast accuracy/cost win).
4. Add the validation + cross-system reconciliation layer (catches the silent errors).
5. Route the residual to a vision model / doc-AI with confidence-gated human review; start the
   correction flywheel.
