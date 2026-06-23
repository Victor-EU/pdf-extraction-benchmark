# How PyMuPDF Parses Tables in This Benchmark

> Scope: explains exactly how PyMuPDF's table machinery (`find_tables()` / `.extract()`) was
> used here, how the algorithm actually works, what it does on this finance corpus, and why the
> result is "extracts characters but loses structure." Companion to `AUDIT_PYMUPDF_STRUCTURE.md`.
> Environment: PyMuPDF **1.26.7** (MuPDF 1.26.12).

---

## TL;DR

- PyMuPDF touches tables in **two separate places**: a page **classifier** (detection only) and the
  **content extractor** (the real `find_tables().extract()` → TSV).
- The benchmark ran `find_tables()` with its **default** strategy: `vertical_strategy="lines"`,
  `horizontal_strategy="lines"` — **not** `lines_strict`, **not** `text`.
- In `lines` mode the table grid is built **purely from drawn vector ruling lines**. Text position
  does **not** decide where a table is; text is used **only to fill cells** after the line grid exists.
  There is no "cross-check text alignment against the borders." (That column-from-text-alignment idea
  is the *separate* `text` strategy, which we did not enable.)
- Consequence on this finance corpus: **bordered regions sometimes detected (but chart strokes
  produce garbled false-positive mini-tables); borderless financial tables — the majority — detected
  as zero.**
- And the extracted table TSV is **not fed to the headline/structure judge** anyway — the judged
  markdown is the flat `get_text("blocks")` reading-order stream. So PyMuPDF's table *structure*
  contributed essentially nothing to its score; its numbers/tokens survived only in the recall-only
  dimension.

---

## 1. Two separate "table methods"

### 1a. Detection — for page *classification* (`scripts/pymupdf_parser.py`)
This script only decides *what kind of page* it is. For tables it calls `page.find_tables()` and uses
two derived numbers:
- `n_tables` — count of detected tables (`pymupdf_parser.py:52`)
- `table_frac` — fraction of page area their bboxes cover, via a 64×64 occupancy grid (`:112`)

Decision rule (`:137`, `:156`):
```python
table_strong = nt >= 1 and taf >= 0.16          # strong signal
... weak fallback:  if nt >= 1 and taf >= 0.08: return "Table"
```
It never reads cell content here — just "is there a grid, and how big is it."

### 1b. Extraction — for *content* scoring (`scripts/collect_extractions.py:64`)
This is the real table "method":
```python
for t in pg.find_tables().tables:
    tables.append("\n".join(["\t".join("" if c is None else str(c) for c in row)
                             for row in t.extract()]))
```
Pipeline: `find_tables().tables` → `t.extract()` (rows × cells, `None` for empty) → serialized as
**TSV** (tabs between cells, newlines between rows). No markdown pipes, no header demarcation.

---

## 2. How `find_tables()` actually works (the default `lines` mode)

Default parameters in 1.26.7 (from `inspect.signature(fitz.table.find_tables)`):

```
vertical_strategy        = lines
horizontal_strategy      = lines
snap_tolerance           = 3
join_tolerance           = 3
edge_min_length          = 3
min_words_vertical       = 3      # only used by the `text` strategy
min_words_horizontal     = 1      # only used by the `text` strategy
intersection_tolerance   = 3
```

**`lines` mode — grid comes from drawn vectors ONLY:**
1. Collect every vector line segment on the page (the "svg" strokes — drawing `op == "l"`, plus
   rectangle edges, since this is `lines` and not `lines_strict`).
2. Keep near-horizontal / near-vertical segments longer than `edge_min_length=3`.
3. **Snap** near-coincident edges to a common coordinate (`snap_tolerance=3` pt) and **join**
   collinear segments across small gaps (`join_tolerance=3`).
4. Compute **intersections** of horizontal × vertical edges (`intersection_tolerance=3`). Four
   intersections enclosing a box = one **cell**. Contiguous cells = one **table**; bbox = their union.
5. **Text fills cells only:** for each cell box, gather the words whose positions fall inside it.

So in the default mode, **text position never decides where a table is** — it only populates cells
*after* the drawn lines define the grid. Detection is purely line-driven.

**`text` mode (NOT used) — the one people usually picture:** infers separators from text alignment —
a vertical edge is posited wherever ≥ `min_words_vertical=3` words line up. *That* is the
"do the columns line up like a table?" check. We never enabled it, and §3 shows why you wouldn't
want it blindly.

`lines_strict` (also not used) would additionally ignore edges that are merely borders of *filled*
rectangles (shading), counting only true stroked lines.

---

## 3. Empirical evidence from the corpus (`IAR_FY25_EN.pdf`)

Sweep of all 310 pages — table count under `lines` (default) vs `text`, plus count of drawn
near-horizontal/near-vertical line segments:

| observation | meaning |
|---|---|
| `text` strategy returns **1 table on nearly every page** | it collapses the whole page into one giant grid — over-merges, useless for separating real tables |
| `lines` returns **0** on many pages with hundreds–thousands of drawn segments (p20: 2705h/1833v; p52: 2903h; p8: 634h) | drawn lines ≠ table; the segments are chart/sparkline strokes that don't intersect into closed cell grids |

Two diagnostic pages:

**p34 — chart/infographic with drawn bars.** `lines` reports "3 tables" — all **false positives**.
Tiny bboxes, garbage cells:
```
table[1] bbox=(370,192,546,298) rows=2 cols=3
  ['217\n53\n164', '38', None]   ← three numbers crushed into one cell, half the cells None
```
The bar/axis strokes happened to intersect into box-like shapes. `lines` mode cannot tell a chart's
rectangles from a table's rules.

**p165 — seven side-by-side remuneration tables.** `lines` finds **0 tables** — those tables are
*borderless* (whitespace-aligned, no drawn rules), so there are no segments to build a grid from.
`text` mode "recovers" them only by merging all seven into one 53×19 super-grid — also useless.
(This is the same page used as Exhibit A in `AUDIT_PYMUPDF_STRUCTURE.md`, where the reading-order
`y/12` band sort interleaves the side-by-side tables row by row.)

---

## 4. The table TSV is collected but NOT judged in the headline

The grid TSV from `.extract()` lands in the `tables` field — but the document the canonical judges
see does **not** include it.

- `build_vendor_md.page_md` (`build_vendor_md.py:18`) builds each vendor's judged markdown from
  `ordered_full` + figure descriptions only. For PyMuPDF, `ordered_full` is the raw
  `get_text("blocks")` reading-order stream, sorted by `(round(y/12), x)`
  (`collect_extractions.py:60`). The `find_tables()` TSV is never spliced in.
- The fair-total + structure-strict + element judges therefore see PyMuPDF as a flat reading-order
  character stream, **no table grid at all** (`AUDIT_PYMUPDF_STRUCTURE.md:36-40`).
- The `tables` TSV is consumed only by `score_extraction.py:55,61` — the recall-only "how much info"
  dimension — where its tokens/numbers are pooled. It props up *recall*, never *structure*.

This is precisely why the verdict is "extracts characters but loses structure": the table-finding
machinery is real, but it is line-dependent, noisy on charts, blind to borderless tables, and routed
around the structural judge anyway.

---

## 5. Was this fair to PyMuPDF?

Defensible, with one honest caveat:

- **For:** a downstream consumer reading PyMuPDF's actual markdown output gets the interleaved block
  stream — the benchmark judges what the tool really emits in reading order, not a privileged
  side-channel.
- **Caveat:** `find_tables()` *does* recover real grids on genuinely bordered tables, and that TSV
  exists in `results/_extract_pymupdf.json` — it's just never routed into the judged document. The
  clean sensitivity check would be to splice the `tables` TSV into `page_md` (replacing/annotating
  table regions) and re-judge, to isolate "PyMuPDF the library can extract bordered tables" from
  "our reading-order assembly flattens them." On this corpus the upside is bounded: borderless tables
  (the finance majority) yield no TSV, and bordered detections are frequently chart-stroke false
  positives (§3).

---

## Reproduce

```bash
cd "PDF parsing test - Finance" && source .venv-docling/bin/activate

# default parameters
python3 -c "import fitz,inspect; print(inspect.signature(fitz.table.find_tables))"

# per-page lines-vs-text table counts + drawn segment counts (the §3 sweep)
# and the p34 / p165 probes are short ad-hoc scripts over Data/IAR_FY25_EN.pdf
```
