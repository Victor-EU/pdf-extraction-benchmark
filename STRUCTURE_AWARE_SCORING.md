# Structure-aware scoring — the canonical metric (2026-06-14)

**What changed.** The headline fair-total metric is now **structure-aware**. A value is credited
only if its **binding is recoverable** — which row, column, series, node, or entity it belongs to.
Tokens that are present but whose bindings are destroyed (scrambled, flattened, or merged) no
longer count as captured, and a value asserted under the *wrong* key is now penalized as a
contradiction. This applies to **all scores, all vendors, all 599 pages, both judge families.**

**Why.** This corpus is finance / M&A / consulting material. There, *a number bound to the wrong
row is an active downstream error* — strictly worse than an omission, which is at least visibly
missing. The previous rubric measured **information presence** with paraphrase tolerance, so it
credited tools that recover the right characters even when they destroy the structure those
characters depend on. The PyMuPDF audit ([`AUDIT_PYMUPDF_STRUCTURE.md`](AUDIT_PYMUPDF_STRUCTURE.md))
showed this concretely: a flat reading-order dump of an org chart scored 100 on content even though
the reporting lines and the number→person bindings were gone. Structure matters too much here to
sit in a caveat; it belongs in the score.

**Design (no arbitrary weighting).** We did **not** add a separate "structure" dimension with a
chosen weight (the whole reason `fair_total` exists is to avoid arbitrary dimension-averaging).
Instead we **redefined recall** so that:

- `info_recall` = fraction of the ground truth's information conveyed *such that a reader could
  recover the correct bindings*. Scrambled/flattened/merged content scores low (20–50) even when
  every token is present. **Correct structure described in prose earns full credit** — this is not
  a formatting, layout, or verbosity test. On a page with **no** tabular/diagrammatic structure
  (plain prose, a divider) it reduces to ordinary content recall, so unstructured pages are not
  deflated.
- `unsupported` (fidelity) now explicitly counts an **actively wrong binding** — a value under the
  wrong row/column/entity, or a relationship stated backwards — as a contradiction, so misbinding
  is penalized harder than omission. (A flat dump that asserts no binding is only low-recall, not
  unsupported.)

The rubric is byte-identical across the gpt-5 and Gemini judges (`scripts/score_fair_total_structure.py`
+ `_gemini.py`, the latter importing the former's `PROMPT_HEAD`).

## Result — structure-aware vs content recall, both judge families

| Vendor | gpt-5: content → **structure** | Gemini: content → **structure** |
|---|---|---|
| Gemini 3.5 Flash | 92 → **89** (−3) | 97 → **96** (−1) |
| gpt-5 image ◆ | 91 → **88** (−3) | 97 → **96** (−1) |
| gpt-5 file ◆ | 91 → **87** (−4) | 96 → **95** (−1) |
| LlamaParse (agentic) | 90 → **86** (−4) | 96 → **95** (−1) |
| Gemini 3.1 Flash-Lite | 90 → **86** (−4) | 95 → **94** (−2) |
| Landing AI | 87 → **81** (−6) | 95 → **93** (−2) |
| **PyMuPDF** | 84 → **68** (**−16**) | 84 → **68** (**−16**) |
| **Tesseract** | 64 → **52** (**−12**) | 77 → **67** (**−10**) |

**Structure-aware scoring is the great separator.** Every tool that actually preserves structure
(the vision LLMs, Landing AI, agentic LlamaParse) loses ≤6 pp (gpt-5) / ≤2 pp (Gemini). The two
pure-text-dump tools — PyMuPDF and Tesseract, which recover characters but not structure — lose
**10–16 pp**, identically under both independent judge families. PyMuPDF's `unsupported` (fidelity)
also rises sharply (Gemini judge: 1→10) once misbinding counts as an error.

**Ranking effect.** The top order is stable, but the gaps open into clear tiers: PyMuPDF drops from
"just below the leaders" (84) to a distinct lower tier (68), well beneath Landing AI (81–93) and far
from the Gemini/gpt-5/LlamaParse cluster. The headline number now reflects *downstream usability*,
not raw token coverage.

## Validation — the rubric is surgical, not a blanket deflator

Per-category content → structure (gpt-5 judge):

| | PyMuPDF | Gemini 3.5 Flash | Landing AI |
|---|---|---|---|
| Text (prose) | 91 → 80 (−11) | 97 → 95 (−1) | 95 → 93 (−2) |
| Table | 85 → 71 (−15) | 92 → 87 (−5) | 88 → 80 (−7) |
| Chart/Diagram | 79 → 54 (**−26**) | 87 → 84 (−3) | 80 → 73 (−7) |
| Mixed | 88 → 79 (−9) | 95 → 93 (−2) | 90 → 83 (−6) |
| Cover/Divider | 50 → **51 (≈0)** | 84 → 84 (≈0) | 82 → 80 (−2) |

The penalty scales with how much **binding-bearing structure** a page holds: near-zero on sparse
Cover/Divider pages (nothing to misbind), largest on Chart/Diagram (relationships are the content).
A structure-preserving vendor (Gemini) barely moves on prose (−1) and only modestly on tables (−5);
the text-dumper craters exactly where structure lives (charts −26, tables −15). That differential —
not the absolute drop — is the evidence the metric measures structure, not strictness.

## What is preserved

- **Content recall is kept as a labeled diagnostic** (`results/_fair_total_judging_content.json`,
  `*_gemini_v2_content.json`; shown as a column in `results/FAIR_TOTAL.md`). It answers a real but
  different question — "how much raw information is present, ignoring binding." The **structure gap**
  (content − structure) is itself a vendor property: how much apparent capture fails a binding check.
- **The element-level and figure evals already priced structure** (element diagrams 50 for PyMuPDF;
  figure judge grades graph-data/diagram-structure against the page image). They are unchanged and
  consistent with this headline change.
- All prior audits (`AUDIT_VEND_CAP.md`, `AUDIT_LLAMAPARSE_MODE.md`, `GT_VALIDATION.md`,
  `RECONCILIATION.md`) describe **content-recall-era** experiments; their internal numbers remain
  correct for what they measured and are labeled as content recall.

## Reproduce

```
# structure-aware re-judge, all 599 pages, both families
FT_GT_CAP=16000 FT_VEND_CAP=16000 python3 scripts/score_fair_total_structure.py 8
python3 scripts/score_fair_total_structure_gemini.py 6
python3 scripts/structure_canonical_report.py     # content vs structure, isolated Δ, both families
python3 scripts/fair_total_report.py              # regenerates results/FAIR_TOTAL.md
python3 scripts/by_document.py                    # regenerates results/BY_DOCUMENT.md
```
Cost: gpt-5 $12.40, Gemini $7.54. Caches: `ground_truth/fair_total_structure_judge/`,
`ground_truth/fair_total_structure_gemini/`. Content-rubric backups: `results/*_content.json`.
