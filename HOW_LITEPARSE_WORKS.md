# What LiteParse does, concretely

[LiteParse](https://github.com/run-llama/liteparse) (run-llama, Apache-2.0) is a **local Rust pipeline
that turns a document into position-aware text** — no model, no GPU, no cloud. It is the open-sourced
core of LlamaParse with the VLM (chart/diagram-reading) layer removed. Here is what actually happens
when you call `parser.parse("doc.pdf")`.

## The pipeline

### 1. Normalize to PDF
DOCX/XLSX/PPTX are converted via **LibreOffice**; images (PNG/JPG/TIFF) via **ImageMagick**.
Everything becomes a PDF so there is one downstream path. Born-digital PDFs skip this.

### 2. Pull characters *with coordinates* (PDFium)
It uses **PDFium** (Chrome's PDF engine, via FFI) to extract every glyph with its bounding box —
`x, y, width, height`, font name, font size. The raw material is not "a blob of text" but a **cloud of
positioned characters**. In the Python API this is `page.text_items`, e.g.:

```
TextItem(text='30', x=26.3, y=18.3, width=11.1, height=9.3, font_name='Helvetica,Bold')
```

### 3. OCR — only if needed
If a page's native text layer is **sparse** (a scan, an image-only page), it rasterizes and runs
**Tesseract** (bundled) or an HTTP OCR server you point it at (EasyOCR/PaddleOCR). On born-digital
documents this almost never fires — on the 599-page finance corpus it triggered on ~1 page.

### 4. The actual cleverness — "grid projection"
The core, in `projection.rs`. It takes the cloud of positioned characters and **snaps them onto a 2-D
character grid that mirrors the visual page**, so columns stay in columns and a table stays visually
aligned as monospaced text. Mechanically:

- Quantize each box's left/right/center edges to ¼-point precision and **cluster them into column
  "anchors"** (an anchor needs ≥2 members; singletons dropped, noise filtered).
- Each box gets a `SnapKind` — **Left / Right / Center** — deciding how it aligns to its anchor (with
  a deliberate left-bias so justified text doesn't false-snap right).
- Detect multi-column layouts (a gap wider than ~2× median char width that straddles the page
  midline) and handle rotated text (sidebar labels separated or inlined).
- Render rows in reading order, inserting spaces to preserve the visual gaps.

The philosophy, in run-llama's own words: *"Why build a complex table-detection pipeline when the
model can just read the columns?"* — it **preserves** layout rather than **detecting** structure.

### 5. Emit
Chosen via `output_format`:

| Format | What you get |
|---|---|
| `json` | text + bounding boxes (structured, position-aware) |
| `text` | spatial-grid plain text (layout preserved via spacing) |
| `markdown` | heuristic reconstruction: headings, lists, **pipe tables**, image placeholders, links |

Plus `screenshot()` to render page images — the "fall back to vision when text isn't enough" path for
agents.

## What it does NOT do

Pure heuristics — no model, no GPU, no cloud. Critically, **it never *reads* a figure**: a chart
becomes either scattered axis numbers in the text or, at best, a pipe table; it emits an empty
`![](image_p30_0.png)` placeholder with no description. That line is deliberate — the VLM layer that
reads charts/diagrams is what stays in the paid LlamaParse.

## What that looks like, concretely (from this benchmark)

Two real pages show both faces of the grid-projection step.

**Clean win — SOTER p90:** the grid recovered a real table.

```
| Subscriptions | 36,338 | 22,207 | 58,624 |
|---|---|---|---|
| ● Fixed       | 16,828 | n.a    | n.a    |
| ● Mobile      | 19,510 | 22,207 | 58,624 |
```

PyMuPDF on the same page dumped those numbers as a flat list with the row/column bindings lost.

**Failure — IAR p258:** on a two-column page it flattened the columns together, interleaving an EPS
table's cells with unrelated segment prose:

```
... | Adjusted net income | Adjusted net income | Segments based on a Prime / Non-Prime distinction | ...
```

The characters are all there; *which number belongs to which row* is not.

## Why this matters for the benchmark

That single mechanism — grid projection — is both why LiteParse beats a raw PyMuPDF dump on
prose/simple tables and why it scored **below** PyMuPDF on dense finance tables (62% vs 68%
structure-aware): when the projection guesses the column structure wrong, it asserts a layout that is
*actively misleading* rather than just dumping text. See [`LITEPARSE_ADD.md`](LITEPARSE_ADD.md) for the
full benchmark result and [`FINAL_REPORT.md`](FINAL_REPORT.md) for where it lands among all ten
vendors.
