# Can regex replace the LLM judge? — deterministic binding-aware scoring POC (2026-06-14)

**Question (user).** The headline metric is a blind LLM judge. Can a deterministic/regex scorer
reproduce it for the cases that *should* be mechanical — verbatim text, table cells, chart data
values — leaving the LLM only for inherently descriptive diagrams? The refinement that makes this
non-trivial: **score the structure too** — break tables/charts into single labeled data points and
check the bindings, since the canonical metric is structure-aware (a value under the wrong row is an
active error).

**Answer.** Partially, and only at one resolution. A deterministic **binding-aware** scorer
(`scripts/poc_binding_score.py`) independently reproduces the single most important headline result —
*structure-destroying text-dumpers (PyMuPDF, Tesseract) collapse into a lower tier* — **with no LLM,
no API, no model variance.** But it cannot be the score: it is a coarse **vendor-aggregate tier
classifier on text + tables only**, not a per-page score, not a fine-ranker within the leader
cluster, and not usable at all on charts or diagrams. The reasons are fundamental, not tuning.

---

## The metric

ATOM = `(normalized_number, {alpha label tokens on the same line})`. Numbers are an **exact oracle**
on this born-digital corpus, so a match is certain (high precision). Two scores per page:

- **numeric_recall** — GT number present *anywhere* in the vendor (the naive set metric).
- **binding_recall** — GT atom matched by a vendor atom with the *same number* whose own same-line
  label set covers ≥ TAU (=0.5) of the GT atom's labels. I.e. *did the number survive WITH its
  row/series label.*

Sources are byte-identical to the LLM judge (`_gt_markdown.json`, `_extract_<v>.json` via
`build_vendor_md.page_md`). Compared against both judge rubrics (structure-aware canonical +
content-presence diagnostic).

> **Harness bug found & fixed mid-POC.** v1 read the pre-concatenated `vendor_md/*.md` and split on
> `\n## ` — but **LandingAI emits markdown `##` subheaders inside page bodies**, so its pages were
> silently truncated at the first inner header. This deflated *only* LandingAI (num_recall 82→93
> after the fix) and made it dominate the disagreement list. A 6th instance of the project's
> recurring pattern: *a measurement artifact deflates exactly one vendor.* Always score from the
> structured per-page JSON, never the concatenated doc.

---

## Result — vendor aggregates (TAU=0.5)

| vendor | numeric_recall | **binding_recall** | judge_struct | judge_content |
|---|---:|---:|---:|---:|
| gemini_flash | 97 | 83 | **90** | 92 |
| gpt5_image ◆ | 98 | 88 | **89** | 92 |
| llamaparse (agentic) | 97 | 93 | **87** | 90 |
| landingai | 93 | 77 | **83** | 88 |
| **pymupdf** | 96 | **74** | **70** | 85 |
| **tesseract** | 74 | **44** | **55** | 66 |

**The core win.** `numeric_recall` saturates everyone at 96–98 *except* Tesseract — it **cannot tell
PyMuPDF (96) from the leaders (97–98)**, reproducing the exact bug the structure-aware migration
fixed. `binding_recall` drops PyMuPDF to 74 and Tesseract to 44, opening the tier gap the LLM judge
sees (70 / 55). Binding is what de-saturates the deterministic metric.

## Result — the metric is surgical (per category, num / bind / judge_struct)

| | gemini | gpt5 | landingai | llamaparse | **pymupdf** | **tesseract** |
|---|---|---|---|---|---|---|
| Text | 99/86/96 | 99/94/96 | 97/82/93 | 99/98/96 | 96/**90**/79 | 78/35/80 |
| Table | 99/94/87 | 98/96/85 | 96/84/81 | 99/98/85 | 98/**80**/72 | 79/54/51 |
| Chart/Diagram | 92/67/84 | 94/72/83 | 86/60/74 | 91/80/77 | 93/**43**/54 | 64/29/34 |

The deterministic penalty lands **where structure lives**: PyMuPDF holds binding on prose (text
90), loses it on tables (80) and craters on charts (43) — the same shape as the LLM judge's
content→structure profile (text −11, table −15, chart −26 in `STRUCTURE_AWARE_SCORING.md`). That
differential is the evidence binding_recall measures structure, not strictness.

---

## The three walls (why it can't be the score)

**1. Per-page, it is only weakly correlated with the judge — and binding does *not* beat numbers.**

| subset | n | binding_recall ~ judge | numeric_recall ~ judge |
|---|---:|---:|---:|
| Text+Table | 1584 | r=0.36 | r=0.40 |
| Chart/Diagram | 888 | r=0.47 | r=0.52 |

Binding helps at the **aggregate** level (tiering) but adds serialization/paraphrase *variance* at
the page level, so per-page it is no better than the naive metric. The judge is doing semantic work
deterministic matching cannot. → **No per-page substitution.**

**2. Charts: line-granularity is a serialization choice, not a fidelity property.** GT serializes a
donut as one line (`0-2 years 18%; 2-5 years 35%; …`); gpt5 serializes one point per line
(`- 18-25: 2%`). Both preserve the binding perfectly, but same-line label overlap → ≈0, so a
flawless extraction (SOTER p93, judge=100) scores binding **0**. Worse, when the series key is
itself numeric (age ranges, years), there are *no alpha labels to match on at all*. Lowering TAU
does not help — the vendor's per-line label set is empty. This is the same paraphrase problem that
drove the project off lexical scoring in the first place, now in structural form. → **Charts are
LLM-only, alongside diagrams.**

**3. The metric is blind to non-numeric structure.** PyMuPDF Alpha p131 is a ~20-column zoo×feature
matrix that PyMuPDF flattened into a scrambled name list — bindings destroyed, judge=4. binding_recall
gave **100**, because the page is nearly number-free and the few numeric atoms hit spuriously.
Qualitative tables (feature matrices, taxonomies) and *all* diagrams carry their structure in words,
not numbers. → **A numeric-binding metric cannot see them; needs a low-numeric-density gate that
hands those pages to the LLM.**

**Fundamental asymmetry behind all three:** a deterministic binding *match* is certain (born-digital
oracle), but a *miss* is ambiguous — "binding destroyed" (PyMuPDF, true signal) vs "serialization /
paraphrase we can't parse" (Gemini's transpose, gpt5's point-per-line, false penalty). You get a
trustworthy **lower bound**, never an upper bound.

---

## Recommended role (not a replacement — a triangulating validator)

This is the project's signature move (the text-layer diff that validated the GT; the 5
measurement-bug catches). Ship the deterministic scorer as:

1. **A free, reproducible, zero-variance corroboration of the headline tiering** on text + tables —
   "structure-destroyers collapse" proven without invoking the model that's also being judged.
2. **A numeric-fidelity floor** — born-digital numbers are an oracle; report deterministic number
   recall as a hard lower bound per vendor.
3. **A judge-disagreement flag** — pages where |binding_recall − judge| is large are where a 6th
   measurement bug would hide. This run already surfaced one real one (the `vendor_md` split bug)
   and confirmed several judge calls are correct against scrambled dumps.

**Do not** publish it as a per-page score, a leader-cluster ranking, or any chart/diagram number.
Diagrams and charts stay with the blind LLM vision/transcription judge — exactly as the user scoped.

Reproduce: `python3 scripts/poc_binding_score.py` (TAU env-tunable) → `results/_poc_binding.json`.
