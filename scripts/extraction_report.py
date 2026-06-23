#!/usr/bin/env python3
"""Assemble the final extraction-quality capability matrix (objective + figure dims)
segmented by page category, and write results/EXTRACTION_COMPARISON.md."""
import json
from collections import defaultdict

VEND_LABEL = {
    "gpt5_image": "gpt-5 (image)", "gpt5_file": "gpt-5 (file)",
    "gemini_flash": "Gemini 3.5 Flash", "gemini_flash_lite": "Gemini 3.1 Flash-Lite",
    "landingai": "Landing AI",
    "llamaparse": "LlamaParse", "pymupdf": "PyMuPDF", "tesseract": "Tesseract",
    "liteparse": "LiteParse", "mistral": "Mistral OCR 4",
}
ORDER = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
         "landingai", "llamaparse", "mistral", "pymupdf", "tesseract", "liteparse"]
# coordinate-grounding capability (does the vendor emit element positions?)
COORDS = {"gpt5_image": "coarse", "gpt5_file": "coarse",
          "gemini_flash": "coarse", "gemini_flash_lite": "coarse", "landingai": "exact boxes",
          "llamaparse": "exact boxes", "pymupdf": "exact boxes", "tesseract": "word boxes",
          "liteparse": "exact boxes", "mistral": "exact boxes"}
COST = {"gpt5_image": "$13.82", "gpt5_file": "$12.54",
        "gemini_flash": "$7.12", "gemini_flash_lite": "$1.12",
        "landingai": "paid", "llamaparse": "paid (agentic)",
        "pymupdf": "$0", "tesseract": "$0", "liteparse": "$0 (local)",
        "mistral": "$5/1k pages"}


def pct(x):
    return f"{100*x:.0f}%" if x is not None else "–"


def main():
    obj = json.load(open("results/_extraction_objective.json"))
    fig = json.load(open("results/_figure_judging.json"))
    key = {(e["doc"], e["page"]): e["final_label"]
           for e in json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))["pages"]}

    # aggregate figure scores per vendor: overall + by category
    g_all = defaultdict(list); d_all = defaultdict(list)
    g_cat = defaultdict(lambda: defaultdict(list)); d_cat = defaultdict(lambda: defaultdict(list))
    n_graph_pages = n_diag_pages = 0
    for r in fig:
        if r.get("error"):
            continue
        cat = key.get((r["doc"], r["page"]), "?")
        has_g = bool(r.get("graphs")); has_d = bool(r.get("diagrams"))
        n_graph_pages += has_g; n_diag_pages += has_d
        for vd, s in r.get("scores", {}).items():
            gs, ds = s.get("graph_score"), s.get("diagram_score")
            if has_g and gs is not None:
                g_all[vd].append(gs); g_cat[vd][cat].append(gs)
            if has_d and ds is not None:
                d_all[vd].append(ds); d_cat[vd][cat].append(ds)

    def mean(xs): return sum(xs) / len(xs) / 100 if xs else None

    L = []
    def w(s=""): L.append(s)

    w("# Extraction-Quality Comparison — how completely each vendor recovers a page's information")
    w("")
    w("> **⁂ The Landing AI row is the legacy pre-DPT-2 endpoint.** This element-level eval has **not** "
      "been re-run on the current `dpt-2-latest` model (only the headline fair total was; see "
      "[`../LANDINGAI_DPT2_REBENCH.md`](../LANDINGAI_DPT2_REBENCH.md)). DPT-2 raised Landing AI's "
      "structure-aware table 80→86 and chart 73→78, so treat the Landing AI numbers below as a "
      "**floor**. Every other vendor is current.")
    w("")
    w("\"Full extraction\" = **text + tables + diagram descriptions + graph data + spatial layout** "
      "(the four dimensions Landing AI's output embodies). Scored on the 599-page corpus, segmented by "
      "the v3 page-category labels. Two metric families:")
    w("- **Objective** (vs a vendor-neutral reference = born-digital text-layer ∪ image-region OCR): "
      "content-token recall, numeric/finance recall, table emission, reading order.")
    w("- **Figure judging** (blind gpt-5 vision judge vs the page image, all 10 vendors shuffled A–J): "
      f"graph-data fidelity over {n_graph_pages} graph pages, diagram-structure fidelity over "
      f"{n_diag_pages} diagram pages.")
    w("")
    w("## The capability matrix")
    w("")
    w("| Vendor | Content recall | Numbers (finance) | Table recovery | **Graph data** | **Diagram struct** | Reading order | Coordinates | Cost (599pp) |")
    w("|---|---:|---:|---:|---:|---:|---:|:--:|---:|")
    for vd in ORDER:
        o = obj[vd]["overall"]
        w(f"| {VEND_LABEL[vd]} | {pct(o['recall'])} | {pct(o['nrec'])} | {pct(o['table_presence'])} | "
          f"**{pct(mean(g_all[vd]))}** | **{pct(mean(d_all[vd]))}** | {pct(o['tau'])} | "
          f"{COORDS[vd]} | {COST[vd]} |")
    w("")
    w("> Reading-order is Kendall-τ vs the reference order; PyMuPDF's is inflated because the reference "
      "uses the same layout engine — read it as a capability flag, not a ranking. Coordinates column is "
      "a capability: parsers emit exact boxes; gpt-5 emits only coarse positions.")
    w("")
    w("> **Table recovery** = on pages whose dominant content is a table (the 128 `Table`-labeled pages), "
      "did the vendor emit a structured table? `Mixed` pages are deliberately excluded — ~half are "
      "chart+text/infographic with no table, so requiring one there punished principled abstention "
      "(Landing AI) and rewarded layout→table over-emission (the accurate-tier LlamaParse emitted a table on "
      "every no-table Mixed page checked; agentic LlamaParse instead tabulates chart data, which is genuine "
      "capture). Landing AI is also credited when its ADE renders a photo/logo-embedded "
      "table as a `figure` chunk holding the full table data. The earlier metric (denominator = `Table`∪`Mixed`, "
      f"literal `table` blocks only) is kept in `_extraction_objective.json` as `table_presence_legacy`; "
      "it scored Landing AI 56% — an artifact, not its true ~91% table recovery.")
    w("")
    w("## Graph-data fidelity by category (the finance question)")
    w("")
    cats = ["Chart/Diagram", "Mixed"]
    w("| Vendor | " + " | ".join(cats) + " | overall |")
    w("|---|" + "---:|" * (len(cats) + 1))
    for vd in ORDER:
        cells = [pct(mean(g_cat[vd][c])) for c in cats]
        w(f"| {VEND_LABEL[vd]} | " + " | ".join(cells) + f" | {pct(mean(g_all[vd]))} |")
    w("")
    w("## Diagram-structure fidelity by category")
    w("")
    w("| Vendor | " + " | ".join(cats) + " | overall |")
    w("|---|" + "---:|" * (len(cats) + 1))
    for vd in ORDER:
        cells = [pct(mean(d_cat[vd][c])) for c in cats]
        w(f"| {VEND_LABEL[vd]} | " + " | ".join(cells) + f" | {pct(mean(d_all[vd]))} |")
    w("")
    w("> **LlamaParse diagram caveat.** This figure judge reads each vendor's *figure-typed* blocks; "
      "LlamaParse (agentic) delivers its diagram content as **inline markdown prose**, not figure blocks, "
      "so this metric under-counts it (~30 here). The element-level judge, which reads LlamaParse's full "
      "markdown, scores its diagrams **83** (gpt-5) / **86** (Gemini) — see `results/ELEMENT_AUDIT.md`. "
      "Its graph-data score (77, up from 51 at the accurate tier) rises here because tabulated chart data "
      "lands in its tables. Read the element-level diagram number as the true figure capability.")
    w("")
    w("## Content + numeric recall by category (objective)")
    w("")
    CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]
    w("**Content recall:**")
    w("")
    w("| Vendor | " + " | ".join(c.split("/")[0] for c in CATS) + " |")
    w("|---|" + "---:|" * len(CATS))
    for vd in ORDER:
        bc = obj[vd]["by_cat"]
        w(f"| {VEND_LABEL[vd]} | " + " | ".join(pct(bc[c]["recall"]) for c in CATS) + " |")
    w("")
    w("**Numeric (finance) recall:**")
    w("")
    w("| Vendor | " + " | ".join(c.split("/")[0] for c in CATS) + " |")
    w("|---|" + "---:|" * len(CATS))
    for vd in ORDER:
        bc = obj[vd]["by_cat"]
        w(f"| {VEND_LABEL[vd]} | " + " | ".join(pct(bc[c]["nrec"]) for c in CATS) + " |")
    w("")
    w("## Notes & caveats")
    w("")
    w("- **Gemini 3.5 Flash is the new overall leader on the figure dimensions** — top-tier graph-data "
      "fidelity (85%, level with gpt-5) and a commanding lead on diagram structure (91% vs gpt-5 66–70% / "
      "Landing AI 82%) — at ~half gpt-5's cost. **Gemini 3.1 Flash-Lite** roughly matches Landing AI on "
      "figures (83%/82%) for **$1.12** (12× cheaper than gpt-5). _(Figure dims = no-truncation re-judge, "
      "`AUDIT_VEND_CAP.md`.)_")
    w("- **Judge-is-gpt-5 caveat, now *strengthened*:** the blind vision judge is gpt-5, yet it scored "
      "Gemini's diagrams *above its own* (91% vs 66%) without knowing which extraction was whose. A judge "
      "favouring a competitor over itself is evidence the blind+vs-image design is not self-serving.")
    w("- **Gemini = native-vision LLM, same family as gpt-5:** coarse positions only (no element boxes), "
      "tables/figures recovered as described content. Run in `image` mode (rendered PNG) with the "
      "identical prompt+schema as gpt-5, so the comparison isolates the model. `thinkingLevel=minimal` "
      "(the analog of gpt-5 `effort=low`).")
    w("- **One degenerate page per Gemini model** (`gemini-3.5-flash`: Alpha p5; `gemini-3.1-flash-lite`: "
      "IAR p103) hit the shared 16k-output cap via runaway repetition and scored empty — gpt-5 did both "
      "in ~2k tokens. 1/599 each; aggregates unaffected. A real (small) robustness data point, not a "
      "harness artefact.")
    w("")
    open("results/EXTRACTION_COMPARISON.md", "w").write("\n".join(L) + "\n")
    print("wrote results/EXTRACTION_COMPARISON.md")
    # also echo the matrix
    print("\n".join(L[:24]))


if __name__ == "__main__":
    main()
