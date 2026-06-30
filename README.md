# PDF Extraction Benchmark — Insurance Forms

A structure-aware benchmark of PDF-extraction approaches — vision LLMs, hosted document
parsers, and local text-layer/OCR tools — measured on how much of a **dense, partially-filled
insurance / administrative form** each one recovers **with the bindings intact**.

The headline metric is the **structure-aware fair total**: a value counts only if its binding
is recoverable — *which field label* it belongs to, *which row/column* of a table, and for a
checkbox/radio, *whether it is ticked*. On these forms a value attached to the wrong field, or
a checkbox read as ticked when it is blank, is an **active downstream error** — worse than an
omission — so structure and checkbox state are scored, not caveated.

> This repo is a re-aiming of a prior chart/finance-document benchmark onto an **insurance-form
> corpus**. The chart/diagram/graph machinery is retired; the new structure primitives are the
> **form field** (label → value) and the **checkbox/radio state**. The prior chart/finance reports
> have been retired from the tree; they remain in the git history of the pre-insurance commits.

## Corpus

7 pages of French insurance / social-protection forms (born-digital, partially filled):

| Doc | Pages | What it is |
|---|---|---|
| Unédic *attestation d'employeur* | 4 | Unemployment-insurance employer certificate (employee LAYOUNI Fadhel): employer + employee identity, employment dates, rupture motive, salary tables, checkbox/radio fields. |
| MNH *demande d'aide sociale* | 3 | Health-mutual social-aid application (DRAFT): cover letter, instructions, checkbox-grid aid tables. |

These are **hard**: the fill values sit in a scrambled, space-separated text layer (the NIR
prints as `1 8 4 0 6 2 1 0 5 4 0 1 8`), value→label binding is visual, and checkbox state is
visual-only. No rule-based parser can read them correctly.

## How the ground truth is built (vision, multi-source)

Because the forms can't be read by rules, the key is built from **three independent vision
sources and reconciled** (full method in [`ground_truth/GT_RECONCILIATION.md`](ground_truth/GT_RECONCILIATION.md)):

1. **Gemini 3.5 Flash** with a form-aware schema (`field` label→value, `choice` label+state, `table`) — the structural backbone.
2. **The PDF text layer**, declared authoritative for every printed character/number; every field value is re-grounded against it.
3. **Claude high-res vision** adjudicates the vision-only calls — every one of the 15 checked boxes was confirmed against a high-res crop. Landing AI cross-checks prose/tables.

Gemini (and lightly Landing AI) co-author the key, so their scores against it are an **upper
bound** (`◆`, not ranked). Cleanly graded vendors: **gpt-5, Mistral OCR 4, LiteParse, LlamaParse, PyMuPDF, Tesseract**.

## The two metrics

- **Objective dims** (`scripts/score_extraction.py`, free, deterministic): content / numeric
  recall, precision, reading-order τ, table-presence — scored vs a text-layer∪OCR reference.
  **Caveat:** this reference is text-derived, so a tool that simply dumps the text layer
  (PyMuPDF) scores ~100% **even though it preserves no field bindings and no checkbox state**.
  These dims measure "are the characters present," not "is the form readable."
- **Structure-aware fair total** (`scripts/score_fair_total_structure.py`, LLM judge): the
  headline. Credits a value only if a reader could recover *which field/row/column* it belongs
  to and the *correct checkbox state*; penalises a wrong binding or a wrong tick as a
  contradiction. This is the metric that separates structure-preservers from text-dumpers.

## Status

| Step | State |
|---|---|
| Corpus discovery, render, objective reference | ✅ run (free) |
| Ground truth (Gemini + text layer + Claude hi-res) | ✅ built & reconciled |
| Vendors extracted: PyMuPDF, Tesseract, Gemini, Landing AI, gpt-5, LlamaParse, LiteParse, **Mistral OCR 4** | ✅ |
| Mistral OCR 4 (advanced config) added as 8th vendor — full 5-pass re-judge + splice | ✅ 2026-06-23 ([`MISTRAL_ADD.md`](MISTRAL_ADD.md)) |
| Objective scorecard | ✅ `results/_extraction_objective.json` |
| Structure-aware fair-total judge (headline) | ✅ `results/FAIR_TOTAL.md` |
| **Spatial-relationship ranking** (field/checkbox/cell binding — the form metric) | ✅ `results/SPATIAL_RANKING.md` |
| Cross-family judge (Gemini) — self-preference check | ✅ `results/_fair_total_judging_gemini_v2.json` |
| Landing AI on current **DPT-2** model (`v1/ade/parse`) — legacy endpoint config fixed | ✅ 2026-06-15 |
| Ground truth re-verified against page renders (checkbox states + field values) | ✅ all 15 ticked boxes + key fields confirmed |

**Headline (clean vendors): Mistral OCR 4 #1 at 92%, Pulse (Ultra 2) #2 at 90%, then gpt-5 (image)
80%, then LiteParse (56%) leading the local text-layer tools (PyMuPDF 49 / Tesseract 44, order within
judge noise), LlamaParse last (31%).** Mistral OCR 4 (added 2026-06-23, [`MISTRAL_ADD.md`](MISTRAL_ADD.md))
is the standout: it preserves HTML tables and the checkbox glyphs, so its structure gap is just −1 and it
reads forms near the ◆ Gemini ceiling — *the same tool that was 5th-of-10 and the fabrication outlier on
the chart/finance corpus is the clean #1 here*, because forms have no charts for its annotation layer to
hallucinate on (unsupported drops from 19% there to 8% here). **Pulse (Ultra 2)** (added 2026-06-30,
[`PULSE_ADD.md`](PULSE_ADD.md); runpulse.com on `pulse-ultra-2` + `refine`) is the clean **#2** — a true
vision-tier reader (checkbox state 94%, #2 on both spatial judges) that captures ~2pp less than Mistral
but **fabricates the least of any vendor (4% unsupported, +1 structure gap)** and is strongest on the
scanned document (92%); its cost is latency, `refine` running ~30–150s/page (~10× Mistral). PyMuPDF reads prose perfectly but craters
on forms (loses ~23 pts to the binding check under the gpt-5 judge); the pure text-dumpers collapse
exactly where field/checkbox structure lives. **LiteParse** (run-llama OSS, LlamaParse's core minus the
VLM) keeps label↔value adjacency and the tick glyphs via its grid projection, making it the best
*text-layer* tool on forms (the reverse of the finance corpus), though at the corpus-high 23%
wrong-binding rate. `◆` GT co-authors (upper bound): Gemini 3.5 Flash 99%, Landing AI (DPT-2) 84%.

**For forms, spatial relationship is what matters** ([`results/SPATIAL_RANKING.md`](results/SPATIAL_RANKING.md)):
ranked on field→value / checkbox-state / table-cell binding alone, **Mistral OCR 4 tops both judges at
97%** and gpt-5 (image) follows at **84%**, vs the text-layer tools at **30–39%** (LiteParse leads them
at 39%). The decisive split is **checkbox state**, and it sorts the tools by *how each sees a tick*:
**0%** for the parsers that read the text layer and flatten it (PyMuPDF, LlamaParse — the `[X]` glyph is
there but detached); a noisy partial for the two that don't — Tesseract's pixel OCR (6–31%) and
LiteParse's glyph-preserving grid (22–27%); and **85–100%** only for the vision models (Mistral reads
the ☐/☒ glyph at **100%**). A tick is a near-visual fact; only vision reads it reliably. On forms, a
vision model is not optional.

**Validated with a second judge family:** a Gemini 3.5 Flash judge on the byte-identical rubric also
ranks **Mistral OCR 4 #1 (98%) and gpt-5 (image) #2 (94%)** among clean vendors — the same order as
the gpt-5 judge, so the headline is not self-preference. Absolute scores are judge-dependent (the
Gemini judge grades higher across the board); the cross-judge spread is the real uncertainty band, and
on this n=7 corpus the wide gaps are signal while few-point gaps are noise. Full read:
[`FINDINGS.md`](FINDINGS.md).

## Run it

```bash
cp .env.example .env                                   # VISION_AGENT / OPENAI / GEMINI / LLAMA keys
python3 scripts/render_all.py                          # Data/*.pdf -> renders + manifest
python3 scripts/build_reference.py                     # objective text-layer∪OCR reference (free)

# vision GT sources
python3 scripts/gemini_extract.py gemini-3.5-flash image
python3 scripts/landingai_pass.py ground_truth/render_full ground_truth/landingai_full
python3 scripts/build_gt_insurance.py                 # reconciled GT + answer key

# vendors
python3 scripts/collect_extractions.py pymupdf        # also: tesseract / gemini_flash / landingai
.venv-liteparse/bin/python scripts/liteparse_run.py   # LiteParse (run-llama OSS, local/free)
python3 scripts/collect_extractions.py liteparse
MISTRAL_INPUT=png .venv-mistral/bin/python scripts/mistral_run.py   # Mistral OCR 4 (paid; advanced config)
python3 scripts/collect_extractions.py mistral
python3 scripts/openai_extract.py image               # gpt-5 (paid)
python3 scripts/score_extraction.py pymupdf tesseract landingai gemini_flash   # objective
python3 scripts/build_vendor_md.py                    # per-vendor docs for the judge
python3 scripts/score_fair_total_structure.py         # structure-aware headline (paid, gpt-5 judge)
```

Corpus discovery is automatic (`scripts/corpus.py`, case-insensitive `*.pdf`/`*.PDF`) — drop
your own PDFs in `Data/` and the pipeline picks them up.

## License

[MIT](LICENSE) © 2026 Victor Zhang.
