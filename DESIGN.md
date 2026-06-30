# Design — insurance-form extraction benchmark

## Goal

Compare PDF-extraction approaches on **dense, partially-filled insurance/administrative
forms**, measuring not "did the characters come out" but "**is the form readable downstream**"
— every value bound to its field, every table cell to its row/column, every checkbox to its
true state.

## Why this is a re-aim, not the original benchmark

The original benchmark targeted chart/finance documents; its differentiators were
**chart-data fidelity** and **diagram structure**, and its page taxonomy had
Chart/Diagram/Cover categories. Insurance forms have **none of that**. They are dominated by
two structures that did not exist in the old harness:

- the **form field** — a printed label with a fill-in value (often blank), and
- the **checkbox / radio** — whose information is its **checked/unchecked state**, which is
  *visual-only* (absent from the text layer).

So the reframe:

| Axis | Original (charts/finance) | Now (insurance forms) |
|---|---|---|
| Page taxonomy | Text/Table/Chart-Diagram/Mixed/Cover/Image | **Text / Form / Table / Mixed** |
| Extraction block types | text/table/figure(graph\|diagram\|photo\|logo) | text/heading/**field**/**choice**/table/figure(photo\|logo) |
| Structure unit (binding) | value↔row/col/series/node | value↔**field-label** / row / col, checkbox↔**state** |
| Headline differentiator | chart-data + diagram-structure | **field binding + checkbox-state fidelity** |
| Retired | — | `score_figures.py`, figure/graph judging |

## Pipeline

```
Data/*.pdf
  └─ corpus.py (discover_pdfs)        single source of truth; case-insensitive .pdf/.PDF
  └─ render_all.py                    -> ground_truth/render_full/*.png + _manifest.json
  └─ build_reference.py               -> ground_truth/extraction_ref/  (text-layer ∪ OCR; free)

vendors (each -> results/_extract_<vendor>.json via collect_extractions.py)
  ├─ pymupdf, tesseract               local/free
  ├─ liteparse_run.py                 LiteParse (run-llama OSS, local/free; PDFium + grid projection)
  ├─ mistral_run.py                   Mistral OCR 4 (advanced: ocr-4-0 + html tables + bbox annotation)
  ├─ pulse_run.py                     Pulse / runpulse.com (advanced: pulse-ultra-2 + refine + figure desc)
  ├─ gemini_extract.py, openai_extract.py   form-aware schema (field/choice/table)
  ├─ landingai_pass.py, llamaparse_fetch*.py
  └─ build_vendor_md.py               -> results/vendor_md/<vendor>.md (judge input; VENDORS auto-detected)

ground truth
  └─ build_gt_insurance.py            Gemini backbone + text-layer grounding + Claude hi-res
                                      adjudication -> results/_gt_markdown.json,
                                      ground_truth/GROUND_TRUTH.md, ground_truth/answer_key.json

scoring
  ├─ score_extraction.py              objective dims (free, deterministic)
  └─ score_fair_total_structure.py    structure-aware headline (LLM judge; gpt-5)
```

## The form-aware extraction schema

Every block carries (strict JSON schema, shared byte-for-byte across gpt-5 and Gemini):

```
type:         text | heading | field | choice | table | figure | marginalia | other
field_label,  field_value      (type=field; value "" when the field is blank)
choice_label, choice_state      (type=choice; checked | unchecked | none)
figure_kind:  photo | logo | none
position, content
```

`collect_extractions._from_blocks` renders `field` → `label: value` and `choice` → `[x]/[ ]
label` into the per-page text so the binding and the tick survive into the judged document.

## The two metrics

- **Objective** — recall/precision of text tokens and numbers vs the text-layer∪OCR reference,
  plus reading-order τ and table-presence. Deterministic and free, but **blind to binding and
  checkbox state** (a text dump scores ~100%). Use as a capability diagnostic, not the ranking.
- **Structure-aware fair total** — a blind LLM judge grades each vendor's page document against
  the GT, crediting a value only if its field/row/column **binding is recoverable** and the
  **checkbox state is correct**, and penalising a wrong binding or wrong tick as a contradiction
  (`unsupported`). On a plain-prose page it reduces to ordinary completeness, so prose pages are
  not deflated. This is the ranking metric. Two judge families (gpt-5 + Gemini) share the rubric.

## Ground truth & circularity

The GT is vision-built and reconciled (Gemini + authoritative text layer + Claude hi-res; see
`ground_truth/GT_RECONCILIATION.md`). Because Gemini (and lightly Landing AI) co-author the
key, their scores against it are an **upper bound** (`◆`, reported for context, not ranked).
gpt-5, Mistral OCR 4, LiteParse, LlamaParse, PyMuPDF and Tesseract are graded cleanly. Field *labels* and prose are
independently corroborated by the text layer, so the key's structure is not Gemini-only.

## Corpus-agnostic by construction

No script hardcodes a document list or page count anymore — `corpus.py` discovers `Data/`
and the page taxonomy/answer key are rebuilt per corpus. The `.PDF`-vs-`.pdf` case bug (which
silently dropped a file under macOS glob) is fixed at the discovery layer. Drop new PDFs in
`Data/`, rebuild the GT, and the same pipeline runs.

## Not included

The source PDFs, renders, ground-truth transcriptions and per-vendor reconstructions reproduce
the full content of documents not cleared for distribution; they are gitignored. The code and
findings are published for inspection and adaptation.
