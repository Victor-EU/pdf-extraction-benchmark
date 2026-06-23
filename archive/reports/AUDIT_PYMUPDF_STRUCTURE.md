# Pre-publication audit — does PyMuPDF's content score over-credit STRUCTURE loss?

**Date:** 2026-06-14 · Companion to [`FINAL_REPORT.md`](FINAL_REPORT.md), [`AUDIT_LLAMAPARSE_MODE.md`](AUDIT_LLAMAPARSE_MODE.md),
[`AUDIT_VEND_CAP.md`](AUDIT_VEND_CAP.md), [`GT_VALIDATION.md`](GT_VALIDATION.md).
**Triggered by an industry-expert challenge:** *"PyMuPDF's result looks suspicious. It can surely
extract the content (characters) but it loses the structure — how is it scoring 84%?"*

## Bottom line

**The expert is right about the mechanism, and we quantified it.** PyMuPDF recovers the
born-digital **text layer** (so the right characters and numbers are present) but **loses
structure** — it merges side-by-side tables, and on relational diagrams it destroys the
node→value and reporting-line bindings, leaving floating token clusters. The canonical
**fair-total** metric measures *information presence* with paraphrase tolerance, so it credits
those present-but-unstructured tokens as recall. A controlled re-judge that holds **everything
fixed except the rubric** (information-present → structure-recoverable) costs **PyMuPDF −24.5 pp**
on the 97 relational-diagram pages while every structure-aware vendor moves ≤5 pp. That
differential is the inflation, isolated.

**But it is a *scoping caveat*, not a ranking error.** Relational diagrams are ~16% of the
corpus, and on the born-digital text/table majority PyMuPDF's *within-row* bindings genuinely
survive. Structure-adjusting **all** diagram pages moves PyMuPDF's corpus total only
**84.2 → 80.3**; it stays 5th, above Tesseract, below Landing AI (the gap to Landing AI
*widens*). **Read PyMuPDF's 84% as "recovers ~84% of the page's facts/tokens," NOT "produces
84%-usable structured output."** The structural truth is already in the element-level and
figure evals; this audit reconciles them and makes the caveat explicit.

This is the 5th "a measurement choice moved one vendor" finding in this project — and the first
that *inflates* a vendor (the table_presence artifact, the GT comma-merge, VEND_CAP, and the
LlamaParse tier all *deflated* a vendor).

---

## 1. What PyMuPDF actually feeds the judge

`collect_extractions.collect_pymupdf()` emits, per page, the `get_text("blocks")` text blocks
sorted into reading order by `(round(y/12), x)`. The judged markdown (`build_vendor_md.page_md`)
is **those reading-order text blocks only** — it does not even include PyMuPDF's `find_tables()`
TSV. So PyMuPDF is graded on a pure reading-order character stream with no table grid and no
figure model.

### Exhibit A — a multi-table page (IAR p165, seven small remuneration tables side by side)

PyMuPDF's y-band sort **interleaves two side-by-side tables row by row**:

```
0. Executive Board Member € 3,660,036 € 3,581,446      ← table 1 (by job category)
Female € 48,125 € 46,640                                ← table 4 (median by gender), sitting beside it
1. Senior Management € 381,700 € 380,702                ← back to table 1
Male € 57,488 € 55,550                                  ← back to table 4
```

**Within-row bindings survive** (a label and its two year-values share a y-band and sort
left-to-right correctly), but the **table grouping is destroyed** — seven tables are merged into
one run. Here the row labels are self-describing ("Female", "1. Senior Management"), so a reader
can still mostly recover the facts → the judge's high score is *defensible*. This is the **mild**
end of the structure problem.

### Exhibit B — a relational diagram (SOTER p92, AddSecure org chart) — canonical score: **100**

```
Nils Kjölhede
...
CFO  Sweden: 7 Employees
...
11  1  1  2          ← a bare number row, detached from any person
...
28  21  21  32        ← whose headcounts are these?
```

The node labels and headcounts are all present, but the **reporting hierarchy is gone** and the
**count→person bindings are scrambled into floating clusters** ("11 1 1 2"). You **cannot**
recover that *Nils Kjølhede = CFO = 11 employees* from this dump. Gemini produced a clean tree
with every binding intact. **The canonical judge scored PyMuPDF 100 here** — crediting token
presence and ignoring the destroyed relationships its own rubric nominally asks for. This is the
**severe** end, and it is common: the corpus has **97 relational-diagram pages** (51 SOTER,
36 IAR, 10 Alpha).

---

## 2. Triangulation — three independent judges already disagree about PyMuPDF on figures

On the same figure pages, the content judges and the structure judges diverge sharply **only for
the pure-text-dump tools**:

| Metric (what it actually measures) | PyMuPDF | Gemini 3.5 Flash | Landing AI |
|---|---:|---:|---:|
| Fair-total `info_recall`, Chart/Diagram (paraphrase-tolerant **content**) | **79** | 87 | 80 |
| Element-level, **Charts** (content per element, full md) | 83 | 90 | 85 |
| Element-level, **Diagrams** (content per element, full md) | **50** | 92 | 89 |
| Figure-judge, Graph-data fidelity (vs page **image**) | **29** | 85 | 80 |
| Figure-judge, Diagram-structure fidelity (vs page **image**) | **29** | 91 | 82 |

PyMuPDF's content number (79–83) sits **30–50 pp above** its structure numbers (29–50), whereas
the structure-aware vendors are flat across all rows. *(Fairness note, symmetric with the
LlamaParse diagram caveat: the figure-judge's 29 partly understates PyMuPDF because that judge
reads only figure-typed blocks and PyMuPDF dumps everything as text; the fair structural-content
number for PyMuPDF is the element-level **diagrams = 50**, not 29. Even so, 50 is far below the
lumped fair-total's 79.)*

---

## 3. The controlled test — same pages, same vendors, only the rubric changes

We re-judged all **97 relational-diagram pages** with `scripts/score_structure_strict.py`:
identical GT, identical 8 vendors, identical blind shuffle (same `Random(f"{doc}:{page}")` seed)
and 16k caps. The **only** change is the rubric — `info_recall` now requires that
relationships/bindings/order be **recoverable** ("tokens present but with their bindings destroyed
do NOT count… score 20–50 even though the raw tokens are all there"), while **keeping paraphrase
tolerance** (correct structure stated in prose = full credit, so this is not a format penalty).

**Per-page mean `info_recall`, paired to the canonical fair-total on the same 97 pages:**

| Vendor | canonical | structure-strict | Δ |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 92.3 | 90.6 | **−1.7** |
| gpt-5 image ◆ | 93.0 | 89.9 | −3.2 |
| gpt-5 file ◆ | 93.1 | 89.5 | −3.6 |
| Gemini 3.1 Flash-Lite | 88.2 | 85.8 | −2.4 |
| Landing AI | 87.0 | 81.9 | −5.0 |
| LlamaParse (agentic) | 89.7 | 84.4 | −5.2 |
| **PyMuPDF** | **80.8** | **56.3** | **−24.5** |
| **Tesseract** | **63.1** | **46.0** | **−17.1** |

**The penalty is concentrated in exactly the two pure-text-extraction tools.** If the strict
rubric were merely harsher for everyone, all vendors would fall together; instead the
structure-aware vendors move ≤5 pp and the two character-dumpers fall 17–25 pp. That isolates
**structure loss** as the cause. PyMuPDF's strict 56 also lands neatly between its element-level
diagrams (50) and the lenient lumped content judge (79–81) — three methods, one story.

**The drop tracks diagram complexity, not the rubric.** Of the 97 pages, 53 drop >20 pp and 23
drop >40 pp (the dense multi-node/multi-series charts: SOTER p85 95→30, IAR p160 68→5), but **22
are essentially unchanged** and a few rise (SOTER p87 70→90) — the simple diagrams where
PyMuPDF's layout happens to preserve the bindings. A well-behaved result, not a blanket deflation.

### Corpus-level impact — and the ranking holds

Substituting the strict scores on the 97 diagram pages and keeping canonical recall everywhere
else (canonical weights throughout, to isolate the recall change):

| Vendor | canonical corpus | structure-adjusted | Δ |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 91.8 | 91.6 | −0.3 |
| Gemini 3.1 Flash-Lite | 89.9 | 89.5 | −0.5 |
| LlamaParse (agentic) | 89.6 | 88.8 | −0.8 |
| Landing AI | 87.4 | 86.6 | −0.8 |
| **PyMuPDF** | **84.2** | **80.3** | **−3.9** |
| Tesseract | 63.8 | 61.0 | −2.8 |

Ranking among real vendors is **unchanged** (Flash > Flash-Lite ≈ LlamaParse > Landing AI >
PyMuPDF > Tesseract). PyMuPDF stays 5th; the Landing-AI-to-PyMuPDF gap *widens* from 3.2 to 6.3 pp.
Diagrams are only ~16% of pages, and PyMuPDF is legitimately strong on the born-digital text/table
majority where within-row bindings survive — so the inflation is real but bounded.

---

## 4. Verdict — how to read PyMuPDF's number

1. **The 84% is a valid CONTENT-recall figure** (how much of the page's facts/tokens are present),
   **not** a structure-fidelity figure. For PyMuPDF specifically the two diverge by ~24 pp on
   relational diagrams; for the vision LLMs and Landing AI they don't.
2. **PyMuPDF's real profile is bimodal:** excellent and cheap on prose + born-digital tables
   (within-row bindings survive, exact boxes, $0), but it **destroys relational structure** —
   org charts, process flows, multi-table layouts, and any wide matrix whose meaning lives in
   *which cell is where*. Downstream uses that consume structure (feeding tables to a model,
   following a diagram's logic) should not trust the 84%.
3. **This is already disclosed** in the structure-aware evals: element-level diagrams **50**,
   figure graph-data/diagram-structure **29**, table-recovery **57%**. The headline content
   metric should be cited *with* those, never alone — which `FINAL_REPORT.md` §4–§6 now does.
4. The structure-strict rubric is a **diagnostic probe**, not a proposed replacement metric — it
   deliberately overweights structure to *measure each vendor's structure-sensitivity*. The honest
   read of "usefulness" is task-dependent and lies between the two rubrics; the point is that
   PyMuPDF's position on that spectrum is far more rubric-sensitive than any structure-aware vendor.

---

## 5. Resolution — structure is now scored corpus-wide (2026-06-14)

This audit's bottom line ("scoping caveat, not ranking error") was based on structure-adjusting
**only the 97 relational-diagram pages** (corpus 84.2 → 80.3, −3.9). The user's decision was that
**all scores must price structure** — a value bound to the wrong row is an active downstream error,
not just on diagrams but on every table and mixed page. So the headline metric was redefined
**structure-aware corpus-wide** and re-judged on all 599 pages under both judge families
([`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md)).

The full-corpus structure-aware number for PyMuPDF is **68.3 (−15.9)**, larger than this audit's
diagram-only −3.9, because the binding-strict rubric now also applies to the **128 Table pages**
(side-by-side-table interleaving, e.g. IAR p165) and **113 Mixed pages** — not just diagrams. Per
category the drop is Text −11, Table −15, Chart/Diagram −26, Mixed −9, Cover ≈0. The probe in §3
(diagram-only, −24.5 per-page) remains the cleanest *isolation* of the mechanism; the corpus-wide
−15.9 is the *headline impact*. Both are consistent: the probe measures one page-type, the headline
averages all of them (weighted), with the unstructured majority diluting the per-page diagram hit.

## 6. Reproduce

```
# controlled structure-strict re-judge on the 97 relational-diagram pages
FT_GT_CAP=16000 FT_VEND_CAP=16000 python3 scripts/score_structure_strict.py 8
python3 scripts/structure_strict_report.py        # paired Δ table (this doc, §3)
# (add SS_ADD_MULTITABLE=1 to also re-judge the 128 Table pages)
```
Artifacts: `results/_structure_strict_judging.json`, cache `ground_truth/structure_strict_judge/`,
scripts `scripts/score_structure_strict.py` + `scripts/structure_strict_report.py`. Cost $1.86.
