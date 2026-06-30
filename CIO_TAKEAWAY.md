# Document extraction across finance and insurance — one CIO takeaway

*Synthesis of two sibling structure-aware benchmarks: this **finance** corpus (599 pages of
chart/figure-dense annual reports, consulting decks and M&A memos, 11 tools — see `README.md` /
`FINAL_REPORT.md`) and an **insurance-forms** corpus (dense, partially-filled French insurance /
social-aid forms, 9 tools). Both score the same way — not "how many characters did it recover" but
"is each value still bound to the right place": the right row/column/series in finance, the right
field and checkbox state on forms.*

## The headline you can't unsee

**The same tool was the near-worst extractor on one corpus and the best on the other.** Mistral OCR
4 finished **6th of 11 on finance with the highest fabrication rate of any tool (19% of its output
unsupported** — it invented chart values and even a fake flowchart on graphics it couldn't read).
On insurance forms the *identical* tool, *identical* config, was the **clean #1 at 92%, reading
checkbox state at 100%**, with fabrication down to 8%. Nothing about the model changed — only the
document genre did.

That single fact disproves the question most extraction RFPs are built around. **There is no "best
PDF extractor." There is only the best extractor *for a document type*, and it changes between
document types you already own.**

There is a quieter, complementary lesson in the same data. The hosted parser added right after Mistral
— **Pulse (Ultra 2)** — did *not* swing: it was a clean, low-fabrication vision reader on **both**
corpora (86% / 5% unsupported on finance — the *lowest* fabrication of any vision tool there; clean #2
at 90% on insurance). So genre doesn't just reshuffle the leaderboard — it also separates the tools
whose *fidelity* is stable from the ones whose accuracy is a coin-flip by document type. That stability,
not a single leaderboard rank, is what you actually want to procure for.

## Why the winner flips: two genres, two different hard problems

| | **Finance documents** (reports, decks, memos) | **Insurance forms** (applications, attestations, claims) |
|---|---|---|
| The bottleneck | Reading **graphics** — charts, diagrams, dense multi-column tables | **Spatial binding** — value↔field, and *which box is ticked* |
| Who won | **Gemini 3.5 Flash** (89%); a five-way pack of vision parsers at 86% incl. **Pulse**, the cleanest (5% fabrication) | **Mistral OCR 4** (92%); GPT-5 second (80%); Pulse clean #2 (90%) |
| Who failed | Text-layer dumpers crater (PyMuPDF 68, Tesseract 52) — they recover characters but lose chart data and table structure | Same dumpers crater harder (30–56%) — and score **0% on checkbox state**: the tick is in the text stream but detached from its option |
| The trap | **Fabrication** — a model that can't read a chart may invent plausible numbers (Mistral's 19%) | **Silent misreads** — a national-ID or date-of-birth read confidently wrong; a blank box reported as ticked |

Read across the two columns and the pattern is clear: **the skill that wins finance (reading
graphics) is not the skill that wins forms (reading 2-D position and tick marks)**, so the leaderboard
reshuffles. A vendor bake-off run on your annual reports tells you almost nothing about your claims
forms.

## What holds true in *both* benchmarks (the durable lessons)

1. **"Character accuracy" is the wrong metric, everywhere.** PyMuPDF recovers ~100% of the characters
   and still lost 16 points in finance and collapsed on forms, because a value detached from its row,
   or a tick detached from its option, is not usable data. Insist on **structure-aware evaluation** —
   bindings, not bytes.

2. **The cheap text-layer/OCR tier is disqualified for anything structured.** Free is not a bargain
   when the output destroys the relationships that carry the meaning. It's fine for plain prose; it
   fails on tables, charts, and forms — i.e. on most of what insurers actually process.

3. **Your worst errors are confident and silent.** Finance: invented chart values. Insurance:
   misread PII and false checkbox ticks. Neither announces itself; both flow straight into pricing,
   adjudication, or underwriting. This — not raw accuracy — is the governance risk to design against.

4. **The model is a cheap, swappable commodity.** Both full benchmarks cost single-digit dollars to
   run; in finance the value-frontier tool (Gemini 3.1 Flash-Lite) hit 86% for **$1.12**. Whatever
   leads today will be overtaken within a year. Model choice is your *least* durable decision.

## What to actually do

- **Route, don't standardize.** Build `classify → route → extract → validate → review`. Classify the
  document, route it to the extractor that wins *that genre* (a vision model for charts/figures; a
  form-aware/checkbox-reading model for forms), and keep every model behind a swappable interface so
  changing one is a config edit, not a re-platform. "Just use one model for everything" is the exact
  mistake these two benchmarks independently disprove.

- **Spend on the validation layer, not the model.** Business-rule and cross-field checks, fabrication
  detection, and **confidence-gating on material fields (PII, money, elections, ticks)** with a
  human-review queue for exceptions. This is the durable, defensible asset; the extractor is a
  replaceable part inside it.

- **For regulated, auditable ingestion, weigh the Document-AI tier** (Azure Document Intelligence,
  AWS Textract, Google Document AI, Landing AI ADE). It trades a little peak accuracy for geometry,
  calibrated confidence, and an audit trail — usually worth more in a regulated claims/underwriting
  workflow than the last few accuracy points.

## Bottom line

Stop shopping for *the* extractor and start building the *pipeline* that routes each document to the
right one and catches confident-but-wrong values before they reach a decision. The two benchmarks
agree on the only durable conclusion: **the model is interchangeable and genre-specific; the routing
and validation layer is where the accuracy, the cost control, and the compliance posture actually
live.** And treat any single benchmark number — including ours — as a prompt to measure *your own*
document mix, not as a verdict.
