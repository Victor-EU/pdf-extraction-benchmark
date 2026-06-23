#!/usr/bin/env python3
"""Per-document slice of the fair-total content-recall eval.

Each of the three PDFs is a distinct document GENRE:
  - 20190308_Projet_Alpha_Restitution  = consulting report (French)  [156 pp]
  - IAR_FY25_EN                         = public annual report        [310 pp]
  - SOTER - Company Presentation - vFF  = M&A information memorandum  [133 pp]

Produces two analyses, for BOTH judge families (gpt-5 + Gemini), from the
CANONICAL fair-total judging files (agentic LlamaParse already spliced in):
  1. fair-total content recall per vendor, per document
  2. fair-total content recall per vendor, per (document x page-category)

fair_total = Sum(info_recall x page_info_weight) / Sum(page_info_weight),
computed WITHIN each slice using each judge family's own canonical weights.
The page category for slice 2 is joined from the reconciled answer key.

Writes results/BY_DOCUMENT.md. No re-judging — pure re-aggregation of the
canonical per-page scores, so it is fully reproducible and weight-stable.
"""
import json
from collections import defaultdict

GPT5 = "results/_fair_total_judging.json"            # canonical gpt-5 judge (agentic LP)
GEM  = "results/_fair_total_judging_gemini_v2.json"  # canonical Gemini judge (agentic LP)
KEY  = "ground_truth/reconcile/final_answer_key_v3.json"  # canonical key (GT markdown + FAIR_TOTAL + element/figure all use v3)

DOCS = [
    ("20190308_Projet_Alpha_Restitution", "Alpha", "Consulting report (FR)", 156),
    ("IAR_FY25_EN",                        "IAR",   "Public annual report",   310),
    ("SOTER - Company Presentation - vFF", "SOTER", "M&A info memorandum",    133),
]
CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]
VENDORS = [  # (key, display)  -- ranking-relevant order; gpt-5 flagged upper-bound
    ("gemini_flash",      "Gemini 3.5 Flash"),
    ("gemini_flash_lite", "Gemini 3.1 Flash-Lite"),
    ("llamaparse",        "LlamaParse (agentic)"),
    ("landingai",         "Landing AI"),
    ("mistral",           "Mistral OCR 4"),
    ("pymupdf",           "PyMuPDF"),
    ("liteparse",         "LiteParse"),
    ("tesseract",         "Tesseract"),
    ("gpt5_file",         "gpt-5 file ◆"),
    ("gpt5_image",        "gpt-5 image ◆"),
]


FINDINGS = """## What the per-document slice reveals

*(Numbers are **structure-aware** (bindings must be recoverable). Findings read off the
**gpt-5 judge** — the discriminating one. The Gemini judge compresses the structure-preserving
vendors into 93–96 but separates PyMuPDF/Tesseract identically; both tables are below.)*

**1. The annual report is the easy genre; the M&A memo is the great separator — even more so
under structure-aware scoring.** Every vendor peaks **on IAR** (born-digital prose + clean
labelled tables) and bottoms **on SOTER** (60% chart/diagram pages). On IAR the structure-
preserving vendors converge in a ~1 pp band (Gemini Flash 94, LlamaParse 94, Landing AI 93); on
SOTER they spread 9 pp (Flash 85 → LlamaParse 76) and the full field spreads **47 pp** (down to
PyMuPDF 59, Tesseract 38). **Benchmark only on annual reports and you'd wrongly conclude all
vendors are equivalent.**

**2. Gemini 3.5 Flash wins on all three genres** (83 Alpha / 94 IAR / 85 SOTER), with its widest
lead on the chart-heavy memo — the strongest binding-preserving chart reader. Safe default
regardless of document type.

**3. LlamaParse (agentic) is genre-sensitive.** Tied #1 on the annual report (94) and solid on the
French consulting deck (80), but it slips to **76 on the M&A memo** — its chart reading is good,
not best, so the chart-heavy genre is its relatively weak document.

**4. PyMuPDF drops to a clearly lower tier on every genre once structure is scored** (61 / 77 / 59).
The content-recall inflation is gone: on SOTER it **no longer edges Landing AI — it now trails it
badly (59 vs 78)**, because the chart-heavy memo is exactly where PyMuPDF's character dump loses
the most structure. Its cover cliff in the deck genres persists (Alpha 21, SOTER 23 vs IAR 77 on
text-rich annual-report covers). PyMuPDF remains a cheap, useful *text + born-digital-table* first
pass, but the per-doc numbers now reflect downstream usability, not token presence. See
[`../STRUCTURE_AWARE_SCORING.md`](../STRUCTURE_AWARE_SCORING.md), `AUDIT_PYMUPDF_STRUCTURE.md`.

**5. "Tables are solved" holds only for annual-report tables.** IAR tables score 93–95 across the
structure-preserving vendors (PyMuPDF 81), but the **French consulting deck's tables (Alpha) are
materially harder** — Gemini Flash 79, Landing AI 78, LlamaParse 76, PyMuPDF 62 — denser,
multi-header, French-language tables. Genre, not just element type, drives table difficulty.

**6. Tesseract degrades on every genre and worst on the chart memo** (50 / 60 / 38). A
scanned-document floor, not a born-digital option, in any genre.

**7. LiteParse (run-llama OSS) is a text-layer tool that scores *below* PyMuPDF once structure is
priced in** (55 Alpha / 72 IAR / 51 SOTER → 62 corpus, vs PyMuPDF 68). It is the open-sourced core
of LlamaParse minus the VLM layer, so like PyMuPDF/Tesseract it is **vision-blind** (0 figure
descriptions) and follows the same genre shape — best on the annual report, worst on the chart memo.
The twist: its heuristic "grid-projection" markdown emits far more table/heading *shape* than
PyMuPDF (table-presence 81% vs 57%) and it actually **beats PyMuPDF on plain-text and image/photo
pages** (Text 85 vs 80, Image 54 vs 28), but it **loses on every structured category** (Table 60 vs
71, Chart 45 vs 54, Mixed 71 vs 79): on dense multi-column pages the projection merges adjacent
columns into a jumble whose row/column bindings are unrecoverable, so the table-shaped output earns
no structure credit. Its structure gap (−18, content 80 → structure 62) is the **largest of any
vendor** — it captures the characters but loses the most structure relative to what it captured.
Verdict: a fast, local, Apache-2.0 *text-and-prose* first pass, but on finance/M&A tables and charts
PyMuPDF+fitz's native table extractor is the stronger free baseline, and any vision tool is a tier
above. See [`../LITEPARSE_ADD.md`](../LITEPARSE_ADD.md).

"""


def load_cat():
    ak = json.load(open(KEY))["pages"]
    return {(e["doc"], e["page"]): e["final_label"] for e in ak}


def weighted(rows, vkey, cat=None, catmap=None):
    """Sum(recall*w)/Sum(w) over rows, optionally filtered to a category."""
    num = den = 0.0
    for r in rows:
        if cat is not None and catmap[(r["doc"], r["page"])] != cat:
            continue
        sc = r["scores"].get(vkey)
        if not sc or sc.get("info_recall") is None:
            continue
        w = r.get("weight", 1) or 0
        num += sc["info_recall"] * w
        den += w
    return (num / den) if den else None, den


def fmt(x):
    return f"{x:.0f}" if x is not None else "–"


def slice1(judges, catmap):
    """Per-document overall fair-total. judges = [(label, rows), ...]"""
    out = []
    for jlabel, rows in judges:
        out.append(f"\n### {jlabel} judge\n")
        out.append("| Vendor | Alpha (consulting, FR) | IAR (annual report) | SOTER (M&A memo) | Corpus |")
        out.append("|---|---:|---:|---:|---:|")
        bydoc = {d[0]: [r for r in rows if r["doc"] == d[0]] for d in DOCS}
        for vkey, disp in VENDORS:
            cells = []
            for d in DOCS:
                v, _ = weighted(bydoc[d[0]], vkey)
                cells.append(fmt(v))
            allv, _ = weighted(rows, vkey)
            out.append(f"| {disp} | {cells[0]} | {cells[1]} | {cells[2]} | **{fmt(allv)}** |")
    return "\n".join(out)


def slice2(judges, catmap):
    """Per (document x category) fair-total -- one table per document."""
    out = []
    for jlabel, rows in judges:
        out.append(f"\n## {jlabel} judge — fair-total by category, per document\n")
        for dkey, short, genre, npp in DOCS:
            drows = [r for r in rows if r["doc"] == dkey]
            present = [c for c in CATS
                       if any(catmap[(r["doc"], r["page"])] == c for r in drows)]
            supp = {c: sum(1 for r in drows if catmap[(r["doc"], r["page"])] == c)
                    for c in present}
            out.append(f"\n### {short} — {genre} ({npp} pp)\n")
            hdr = "| Vendor | " + " | ".join(f"{c} ({supp[c]})" for c in present) + " | Doc |"
            out.append(hdr)
            out.append("|---" * (len(present) + 2) + "|")
            for vkey, disp in VENDORS:
                cells = []
                for c in present:
                    v, _ = weighted(drows, vkey, cat=c, catmap=catmap)
                    cells.append(fmt(v))
                allv, _ = weighted(drows, vkey)
                out.append(f"| {disp} | " + " | ".join(cells) + f" | **{fmt(allv)}** |")
    return "\n".join(out)


def main():
    catmap = load_cat()
    gpt5 = json.load(open(GPT5))
    gem = json.load(open(GEM))
    judges = [("gpt-5", gpt5), ("Gemini", gem)]

    doc = []
    doc.append("# Results by document genre\n")
    doc.append("> **Additional analysis (2026-06-14).** The corpus's three PDFs are three different "
               "document *genres*, with very different content profiles:\n")
    doc.append("> | Doc | Genre | Pages | Dominant content |\n> |---|---|---:|---|")
    doc.append("> | **Alpha** | Consulting report (French) | 156 | tables (58) + charts (34) |")
    doc.append("> | **IAR** | Public annual report | 310 | prose (116 Text + 73 Mixed) + tables (54) |")
    doc.append("> | **SOTER** | M&A information memorandum | 133 | charts/diagrams (80 = 60% of pages) |")
    doc.append("\nAll numbers are the **structure-aware fair total** "
               "(`Σ recall×weight / Σ weight`), re-aggregated from the **canonical** "
               "per-page judge scores — a value counts only if its binding (row/column/node) is "
               "recoverable (see [`../STRUCTURE_AWARE_SCORING.md`](../STRUCTURE_AWARE_SCORING.md)). "
               "gpt-5 rows are ◆ upper-bound (transcriber=judge family); read them for context, not "
               "rank. Reproduce: `python3 scripts/by_document.py`.\n")

    doc.append(FINDINGS)
    doc.append("## 1. Fair-total content recall, by document\n")
    doc.append(slice1(judges, catmap))
    doc.append("\n\n## 2. Fair-total content recall, by category within each document\n")
    doc.append("> Column header `Cat (n)` = page support for that category in that document. "
               "Small-support cells (e.g. Image/Photo = 1 page) are anecdote, not signal.\n")
    doc.append(slice2(judges, catmap))

    open("results/BY_DOCUMENT.md", "w").write("\n".join(doc) + "\n")
    print("wrote results/BY_DOCUMENT.md")

    # also echo slice-1 corpus check to stderr-style stdout for sanity
    for jlabel, rows in judges:
        line = {disp: fmt(weighted(rows, vkey)[0]) for vkey, disp in VENDORS}
        print(jlabel, line)


if __name__ == "__main__":
    main()
