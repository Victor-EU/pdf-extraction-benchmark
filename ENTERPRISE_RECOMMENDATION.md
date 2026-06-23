# Enterprise Document Ingestion — Recommendation

*Derived from the structure-aware insurance-form benchmark in this repo (`FINDINGS.md`,
`results/FAIR_TOTAL.md`). Read the **Scope & limits** section last — it bounds how far these
numbers travel.*

## TL;DR

**Do not standardize on a single model ("just use Gemini for everything").** It is the most
tempting wrong conclusion from this benchmark, for two independent reasons:

1. **The numbers don't say what they appear to.** Gemini scored 99% here, but Gemini
   *co-authored the ground truth* (marked `◆`, unranked) — its score is inflated by construction.
   The clean top-tier evidence is **Mistral OCR 4 at 92% (gpt-5 judge) / 98% (Gemini judge)**, then
   **gpt-5 at 80% / 94%**. The honest read is not "Gemini wins" but "**a vision model is required, and
   several are strong.**" And which one leads is *genre-specific*: **Mistral OCR 4 was 5th-of-10 and
   the fabrication outlier on this repo's sibling chart/finance benchmark, yet is the clean #1 here**
   — the same tool, opposite verdict, because forms reward dense OCR + checkbox glyphs and have no
   charts for its annotation layer to invent on. Standardizing on whatever "won" one corpus is exactly
   the mistake this row warns against.
2. **Model accuracy is the least of the problem at scale.** Enterprise ingestion is a *routing,
   validation, and provenance* problem. The right architecture is a **classify → route → extract →
   validate → review** pipeline with the model behind a swappable interface — not one model wired
   to everything.

---

## What the benchmark robustly establishes

These hold across **both** judge families (gpt-5 and Gemini on a byte-identical rubric), so they
are not single-judge artifacts:

| Finding | Evidence |
|---|---|
| **Text-layer extraction alone is disqualified for forms.** PyMuPDF/Tesseract recover the *characters* perfectly yet score ~30–50%, because they destroy value→field bindings and checkbox state. | PyMuPDF: Text 99–100% but Form 29–54% across judges. |
| **Vision is necessary, not optional**, for the binding/checkbox layer. Checkbox state is near-invisible to the text layer; no rule-based parser recovers it reliably. | Spatial-only ranking (`results/SPATIAL_RANKING.md`): **checkbox state = 0%** for the flattening text-layer parsers (PyMuPDF, LlamaParse) under both judges, ≤6–31% for OCR (Tesseract), ≤22–27% for the best-structured text-layer tool (LiteParse, which preserves the `[X]` glyph but noisily); vision tier 85–100%. |
| **Even the best vendors fail silently.** A pixel-level hand audit found a clean top vendor (gpt-5) **misread the NIR and the date of birth** and dropped a checkbox on page 1 — confident, fluent, wrong, on PII fields; the new clean #1 (Mistral OCR 4) **fabricates content on low-signal pages** (8% unsupported overall, up to 25% on the dense indemnity page); the **legacy** Landing AI asserted a **false checkbox tick** (corrected once re-run on DPT-2); LlamaParse returned `NO_CONTENT_HERE` on a watermarked form. None of these announce themselves. | `FINDINGS.md` §2b/§3; `MISTRAL_ADD.md`; `results/_fair_total_judging*.json`; GT verification crops. |
| **No single tool dominates every page type.** Tools that read prose well can still collapse on dense forms; order between the pure text-dumpers (PyMuPDF #3 / Tesseract #4) is within judge noise. | Per-category tables in `FINDINGS.md` §2/§2b. |

**Implication for the cheap end:** "just grab the text layer, it's free" is wrong for forms. The
characters are present; the *form* is not.

---

## Why "one model for everything" breaks

Once you leave a 7-page probe, model accuracy is rarely the binding constraint:

- **No provenance / geometry by default.** Pure-LLM extraction returns text, not "where on the
  page." Regulated ingestion (insurance is PII-heavy) needs click-to-source audit trails and
  per-field confidence to route uncertain items to humans. Document-AI engines (Azure Document
  Intelligence, AWS Textract, Google Document AI, Landing AI ADE) emit bounding boxes + confidence
  natively; LLMs emit fluent prose with no reliable self-confidence.
- **Non-determinism.** Same PDF → different output. Compliance wants reproducible, explainable
  extraction.
- **Cost × latency at volume.** 7 pages cost ~$0.31. At millions of pages, paying frontier-vision
  rates to read cover letters is indefensible — and *less accurate*, because it exposes easy pages
  to hallucination risk for no reason.
- **Data residency / on-prem constraints.** "Send everything to a frontier API" may violate
  residency or contractual terms outright. (This corpus is itself gitignored as identifying data.)
- **Single point of failure.** Models deprecate, rate-limit, and change behavior. The pipeline
  must survive swapping the model.
- **Confident, silent error is worse than a flagged gap.** A wrong value corrupts everything
  downstream and nobody notices; a missing value is at least visible.

---

## Recommended architecture: a routed pipeline

Bet on the pipeline, not the model.

```
            ┌─────────────┐
  PDF  ──▶  │ 1. Classify │  born-digital vs scanned; prose / form / table / photo
            └──────┬──────┘
                   ▼
            ┌─────────────┐
            │  2. Route   │
            └──────┬──────┘
        ┌──────────┼───────────────┬──────────────────┐
        ▼          ▼               ▼                  ▼
   prose /     forms /        scanned /          high-value
   born-digital checkboxes /  photographed        critical fields
   text         complex tables                    (amounts, IDs, dates)
        │          │               │                  │
   text-layer   vision model    OCR + vision      2 independent
   (pdfplumber/  or doc-AI       (+ doc-AI)         methods, flag
   pypdf):       with geometry                       disagreements
   ~free,        + confidence
   deterministic
        └──────────┴───────────────┴──────────────────┘
                   ▼
            ┌─────────────────────────────────────┐
            │ 3. Validate  schema · cross-field    │
            │    arithmetic · business rules ·     │
            │    LLM/deterministic verifier        │
            └──────────────┬──────────────────────┘
                           ▼
            ┌─────────────────────────────────────┐
            │ 4. Confidence-route low-certainty /  │
            │    high-stakes items to human review │
            └─────────────────────────────────────┘
```

1. **Classify cheaply first** — born-digital vs scanned; prose vs form vs table vs photo.
2. **Route by class:**
   - **prose / born-digital text → text-layer** (pdfplumber/pypdf): near-free, deterministic,
     near-perfect. Don't pay a vision model to read a cover letter.
   - **forms / checkboxes / complex tables → vision model or doc-AI with geometry.**
   - **scanned / photographed → OCR + vision.**
3. **Validate, don't trust:** schema checks, cross-field arithmetic (totals foot, dates
   consistent), business rules, and an LLM-or-deterministic verifier. The benchmark's core thesis
   is that *binding-aware validation catches what raw content recall misses.*
4. **Confidence-route to humans** on the uncertain / high-stakes minority — the entire payoff of
   keeping per-field confidence.
5. **Ensemble the few critical fields** (claim amount, policy number, SIRET, dates) with two
   independent methods and flag disagreements — cheap insurance against confident hallucination.

This is corroborated by the sibling chart/finance benchmark: winners shift by **document genre**
(annual reports — vendors converge; chart-heavy memos — wide spread), and no single tool dominated
every element type. Genre-routing beats one-model-fits-all in both corpora.

---

## Where the models actually land

| Tier | Use for | Notes |
|---|---|---|
| **Text-layer** (pdfplumber MIT / pypdf BSD; LiteParse Apache-2.0) | Born-digital prose & simple text | Near-free, deterministic. **Disqualified for forms** — loses bindings + checkbox state. LiteParse (grid projection) is the best of them on forms (56% / 22–27% checkbox) but still a third of the vision tier and the noisiest (23% wrong bindings). |
| **Vision LLM / OCR-4** (Mistral OCR 4, gpt-5, Gemini Flash) | Forms, checkboxes, complex tables | Clean top-tier evidence: Mistral OCR 4 (92%, clean #1 here) and gpt-5 (80%). Mistral's advanced OCR-4 config reads checkbox glyphs at 100% and preserves HTML tables — but it was the fabrication outlier on the finance corpus, so it is a *genre-specific* leader, not a universal one. Gemini Flash is an excellent *default vision tier* — cheap, fast, long-context — but its 99% here is unprovable (it co-authored the key). |
| **Document-AI** (Azure DI, Textract, Google Doc AI, Landing AI ADE **DPT-2**) | Anything needing geometry, confidence, audit trail, determinism | The right call for regulated / human-in-the-loop ingestion. Trades peak free-form accuracy for provenance + calibration. Landing AI's current DPT-2 model reads form fields/checkboxes well (94% checkbox here) *and* emits exact boxes — the one option that gives both. |
| **OCR** (Tesseract, Apache-2.0) | Scanned input as a front-end to the above | Truly free; mangles dense grids on its own. |

**On Gemini specifically:** a strong default for the vision-routed branch — not a reason to route
*everything* through it. "Use it for everything" over-pays on the easy majority, under-delivers on
provenance/confidence, and stakes your compliance posture on one non-deterministic vendor.

**The most durable point:** *model choice is your least durable decision.* This corpus says Mistral
OCR 4 (then gpt-5); the chart/finance corpus said Gemini and put Mistral 5th-of-10; six months from
now it will say something else. The same tool topping one benchmark and trailing the other is the
proof in hand. Architect so the model sits behind a stable `classify → route → extract → validate →
review` interface and swapping it is a config change, not a rebuild.

---

## Scope & limits (read before quoting any number)

This is a **sharp probe, not a procurement benchmark**:

- **n = 2 documents, 7 pages, one language** (French), one family (administrative / insurance
  forms), **born-digital**. No scans, no handwriting, no photographs, no multi-page tables, no
  invoices/contracts/emails.
- **Absolute scores are judge-dependent** (the Gemini judge grades +12 to +34 pts more leniently
  than the gpt-5 judge). Treat the single number "80%" as gpt-5-judge-specific; the cross-judge
  spread is the real uncertainty band.
- **Ground-truth circularity:** Gemini (and lightly the *legacy* Landing AI) co-authored the key, so
  their rows are upper bounds, not rankings. Only gpt-5, Mistral OCR 4, LiteParse, LlamaParse, PyMuPDF, Tesseract are
  graded cleanly. (Landing AI is shown on its current DPT-2 model; it remains `◆` because the legacy LA
  contributed to the key.)

To actually choose tooling, run **your** document mix at volume and measure **field-level
accuracy, confidence calibration, and human-review rate** under your accuracy / cost / latency /
compliance constraints — not a 7-page structure-recall score.
