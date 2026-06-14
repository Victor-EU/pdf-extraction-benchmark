#!/usr/bin/env python3
"""Dump GT markdown + selected vendor extractions for one (doc,page), to hand-audit a judge score.
Usage: python3 scripts/dump_page.py <doc_substr> <page> [vendor1 vendor2 ...]
"""
import json, sys

VEND_FILES = {
    "gt": ("results/_gt_markdown.json", "md"),
    "gemini_flash": ("results/_extract_gemini_flash.json", "ordered_full"),
    "gemini_flash_lite": ("results/_extract_gemini_flash_lite.json", "ordered_full"),
    "landingai": ("results/_extract_landingai.json", "ordered_full"),
    "pymupdf": ("results/_extract_pymupdf.json", "ordered_full"),
    "llamaparse": ("results/_extract_llamaparse.json", "ordered_full"),
    "tesseract": ("results/_extract_tesseract.json", "ordered_full"),
    "gpt5_image": ("results/_extract_gpt5_image.json", "ordered_full"),
    "gpt5_file": ("results/_extract_gpt5_file.json", "ordered_full"),
}

def find(path, field, doc_sub, page):
    for r in json.load(open(path)):
        if doc_sub.lower() in r["doc"].lower() and r["page"] == page:
            return r.get(field, "")
    return "<<not found>>"

def main():
    doc_sub = sys.argv[1]; page = int(sys.argv[2])
    vendors = sys.argv[3:] or ["gt", "pymupdf", "gemini_flash", "landingai", "tesseract"]
    for v in (["gt"] + [x for x in vendors if x != "gt"]):
        path, field = VEND_FILES[v]
        txt = find(path, field, doc_sub, page)
        if isinstance(txt, list):
            txt = "\n".join(str(x) for x in txt)
        txt = (txt or "").strip()
        cap = txt if len(txt) < 4000 else txt[:4000] + f"\n…[+{len(txt)-4000} chars]"
        print(f"\n{'='*70}\n### {v.upper()}  ({len(txt)} chars)\n{'='*70}\n{cap}")

if __name__ == "__main__":
    main()
