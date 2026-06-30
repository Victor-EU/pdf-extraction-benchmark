# What this benchmark means for insurance CIOs

*Plain-language takeaway from the structure-aware insurance-form benchmark in this repo
(`FINDINGS.md`, `ENTERPRISE_RECOMMENDATION.md`). The corpus is dense, partially-filled French
insurance / social-aid forms (a Pôle emploi employer attestation, an MNH aide-sociale application),
scored not on "characters recovered" but on whether each value stays bound to its field, each tick
to its option, and each cell to its row × column.*

## The one reframe that matters

**The metric your OCR vendor sells you on — "99% character accuracy" — is the wrong metric for
insurance forms.** A parser can recover every character on a benefit application and still be
useless, because it dumps the values in a flat stream detached from their labels and loses which
boxes were ticked. On this benchmark the cheap text-layer tools (PyMuPDF, raw OCR) scored a perfect
~100% on "characters present" yet **29–49% once you require the value to be attached to the right
field and the right checkbox state**. The form survives as text; it does not survive as a *form*.
For insurance — where the meaning is "is this rider elected," "what's the SIRET," "which rupture
code," "what's the date of birth" — that gap is the whole risk.

## What the data says, in plain terms

- **The checkbox is the tell, and it splits the entire market.** Which box is ticked — coverage
  elections, consent, yes/no eligibility — is a near-visual fact. Tools that read the PDF's text
  layer and flatten it (PyMuPDF, LlamaParse) scored **0%** on checkbox state: the `[X]` is in the
  data stream but unmoored from its option. Only models that actually *look at the pixels* read it
  reliably (85–100%). **If checkbox/election fidelity matters to you, a vision model is not
  optional** — and most of insurance's hardest documents are checkbox-and-field forms.

- **The best tool here was not the obvious one — and that's the durable lesson.** Mistral OCR 4 was
  the clean #1 (92% structure-aware, checkbox 100%), ahead of GPT-5 (80%). A second doc-AI vendor,
  Pulse (Ultra 2), landed right behind at 90% and fabricated the *least* of any tool — so this isn't
  one lucky brand: two independent vision engines top the list, and the dividing line is vision-vs-
  text, not vendor. But *the same Mistral was
  5th-of-10 and the worst hallucinator* on our sibling finance/chart benchmark. Forms reward its
  strengths (dense text, table structure, reading ticks) and remove its weakness (no charts to
  invent on). **The right extractor is a property of the document type, not the tool.** Whatever
  "won" a vendor bake-off on one document family can lose badly on the next.

- **Your worst failures will be confident and silent.** Hand-auditing the leaders against the
  pixels: GPT-5 misread a national-ID number and a date of birth — fluent, confident, wrong, on
  exactly the PII fields a downstream system trusts. Mistral fabricated content on near-empty pages
  (up to 25% unsupported on a dense indemnity page). An older parser asserted a checkbox as ticked
  when it was blank. **None of these announce themselves.** This is the insurance-specific danger:
  not a visible blank you'll catch, but a plausible wrong value that flows straight into
  adjudication or underwriting.

## What to do about it

- **Don't standardize on one model.** Model choice is your *least durable* decision — it'll be wrong
  within a year. Architect for `classify → route → extract → validate → review`, with the extraction
  model behind a swappable interface so changing it is config, not a rebuild.

- **Spend on the validation layer, not the model.** The model is cheap (this whole run cost a few
  dollars). Your real assets are business-rule checks, cross-field validation, confidence-gating on
  material fields, and a human-review queue for exceptions. **Surface confidence and gate
  PII/financial fields regardless of which vendor leads** — even the #1 fabricates on low-signal
  pages.

- **For regulated, auditable ingestion, weigh the Document-AI tier** (Azure Document Intelligence,
  AWS Textract, Google Document AI, Landing AI ADE). It trades a little peak accuracy for geometry,
  calibrated confidence, and an audit trail — which in a regulated claims / underwriting workflow is
  often worth more than the last few accuracy points.

## Bottom line

For insurance, the extraction *model* is a commodity that you should expect to swap; the *pipeline*
— routing by document type, validating bindings and checkbox state, and gating confident-but-wrong
values on PII and money before they reach a decision — is the durable, defensible investment. Buy
accordingly, and treat any single benchmark number (including ours — it's a sharp 7-page probe, not
a procurement test) as a reason to run *your* document mix, not as a verdict.
