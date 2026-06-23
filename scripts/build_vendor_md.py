#!/usr/bin/env python3
"""Reconstruct each vendor's FULL 599-page markdown document from its collected extraction,
in reading order (text + tables already ordered, figure descriptions appended per page).

These are the per-vendor documents diffed against ground_truth/GROUND_TRUTH.md by the
document-level "fair total" judge (score_fair_total.py). Also writes readable consolidated
files so the comparison can be eyeballed.

Output: results/vendor_md/<vendor>.md  (one per vendor)
Usage:  python3 scripts/build_vendor_md.py            # all vendors
"""
import os, json

VENDORS = ["gpt5_image", "gpt5_file", "gemini_flash", "gemini_flash_lite",
           "landingai", "llamaparse", "pymupdf", "tesseract", "liteparse", "mistral"]


def page_md(rec):
    """Full-fidelity markdown for one page: ordered text+table blocks, then figure descriptions."""
    parts = list(rec.get("ordered_full") or rec.get("ordered_texts") or [])
    figs = rec.get("figures", [])
    if figs:
        parts += [f"[{f.get('kind','figure')}] {f.get('content','')}".strip() for f in figs]
    return "\n".join(p for p in parts if p and p.strip()).strip()


def load_pages(vendor):
    """(doc,page) -> page_md string.
    LA_DPT2 env: re-benchmark hook — serve the `landingai` slot from the DPT-2 extract so the
    canonical judges score DPT-2 in LA's position with byte-identical prompts otherwise."""
    fn = vendor
    if vendor == "landingai" and os.environ.get("LA_DPT2"):
        fn = "landingai_dpt2"
    data = json.load(open(f"results/_extract_{fn}.json"))
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
