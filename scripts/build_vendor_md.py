#!/usr/bin/env python3
"""Reconstruct each vendor's FULL markdown document (all corpus pages) from its collected
extraction, in reading order: ordered text + tables, then field/choice lines and figure
descriptions per page.

NOTE: the structure-aware judge (score_fair_total_structure.py) consumes vendor text via
`load_pages()` here, which reads results/_extract_<vendor>.json DIRECTLY — the .md files written
below are human-eyeball artifacts only and do not feed the score. The judge target is the per-page
ground truth in results/_gt_markdown.json (readable form: ground_truth/GROUND_TRUTH.md).

Output: results/vendor_md/<vendor>.md  (one per vendor)
Usage:  python3 scripts/build_vendor_md.py            # all vendors
"""
import os, json

# Canonical display order. VENDORS is filtered at import to those actually extracted
# (results/_extract_<vendor>.json present), so a free-only run — e.g. just pymupdf +
# tesseract — works without the paid vendors having been run. Override with the
# VENDORS env var (comma-separated) to pin an explicit set.
ALL_VENDORS = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
               "landingai", "llamaparse", "pymupdf", "tesseract", "liteparse", "mistral", "pulse"]


def available_vendors():
    env = os.environ.get("VENDORS")
    if env:
        return [v.strip() for v in env.split(",") if v.strip()]
    return [v for v in ALL_VENDORS if os.path.exists(f"results/_extract_{v}.json")]


VENDORS = available_vendors()


def page_md(rec):
    """Full-fidelity markdown for one page: ordered text+table blocks, then figure descriptions."""
    parts = list(rec.get("ordered_full") or rec.get("ordered_texts") or [])
    figs = rec.get("figures", [])
    if figs:
        parts += [f"[{f.get('kind','figure')}] {f.get('content','')}".strip() for f in figs]
    return "\n".join(p for p in parts if p and p.strip()).strip()


def load_pages(vendor):
    """(doc,page) -> page_md string.
    LA_DPT2 env: serve the `landingai` slot from the DPT-2 extract (re-benchmark hook)."""
    if vendor == "landingai" and os.environ.get("LA_DPT2"):
        vendor = "landingai_dpt2"
    data = json.load(open(f"results/_extract_{vendor}.json"))
    return {(r["doc"], r["page"]): page_md(r) for r in data}


def main():
    os.makedirs("results/vendor_md", exist_ok=True)
    for vd in VENDORS:
        pages = load_pages(vd)
        keys = sorted(pages)
        L = [f"# {vd} — full extraction ({len(keys)} pages)\n"]
        for k in keys:
            L.append(f"\n\n---\n\n## {k[0]} — page {k[1]}\n")
            L.append(pages[k] or "*(empty)*")
        open(f"results/vendor_md/{vd}.md", "w").write("\n".join(L) + "\n")
        chars = sum(len(v) for v in pages.values())
        print(f"  {vd:<22} {len(keys)} pages, {chars:,} chars -> results/vendor_md/{vd}.md")


if __name__ == "__main__":
    main()
