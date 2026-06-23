#!/usr/bin/env python3
"""Build the form-aware GROUND TRUTH for the insurance corpus (vision, multi-source).

These documents are dense, partially-filled French administrative / insurance FORMS. No
rule-based extractor can read them (the fill values sit in a scrambled, space-separated
text layer and the checkbox STATES are visual only). So the ground truth is built the way
the original benchmark built its key — from intelligent VISION sources, reconciled — but
re-aimed at forms:

  SOURCES (3, independent):
    1. Gemini 3.5 Flash  — the form-aware extractor (field label->value, checkbox/radio
       label + checked|unchecked state, tables). Structural backbone.
    2. The PDF TEXT LAYER — AUTHORITATIVE for every printed character/number. Every Gemini
       field value is validated against it (recombining the space-separated digits); a value
       not grounded in the text layer is flagged for review, not trusted blindly.
    3. Claude (high-res vision) — adjudicates the vision-only calls. EVERY checkbox Gemini
       marked `checked` was confirmed against a high-res crop of the page (see
       ground_truth/GT_RECONCILIATION.md); Landing AI's chunks cross-check text/tables.

  RECONCILIATION: Gemini's blocks are the backbone; the CORRECTIONS overlay below carries
  every hand-adjudicated fix (keyed by doc-key, page, and a match string). Field values are
  re-grounded in the text layer at build time.

  CIRCULARITY: Gemini (and, lightly, Landing AI) co-authored this key, so their scores
  against it are an UPPER BOUND (marked ◆ in the report) and are reported for context, not
  ranked — exactly as the original benchmark flagged its gpt-5-built reference. The cleanly
  graded vendors are gpt-5, LlamaParse, PyMuPDF, Tesseract.

Output: results/_gt_markdown.json (judge target) + ground_truth/GROUND_TRUTH.md (readable)
        + ground_truth/answer_key.json (form-taxonomy page categories).
Usage:  python3 scripts/build_gt_insurance.py
"""
import os, re, sys, json
import fitz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import discover_pdfs, short_label

GEMINI_EXTRACT = "results/_gemini_gemini_flash_extract.json"

# Page-category answer key (form taxonomy: Text | Form | Table | Mixed), assigned by
# inspection of the rendered pages (see GT_RECONCILIATION.md).
PAGE_CATEGORIES = {
    ("AE_33369592200463_17082__LAYOUNI_Fadhel__04022019_20190212145137703", 1): "Form",
    ("AE_33369592200463_17082__LAYOUNI_Fadhel__04022019_20190212145137703", 2): "Form",
    ("AE_33369592200463_17082__LAYOUNI_Fadhel__04022019_20190212145137703", 3): "Table",
    ("AE_33369592200463_17082__LAYOUNI_Fadhel__04022019_20190212145137703", 4): "Mixed",
    ("D.MNH.PR.ASAL.GESTIO.GEDMFI000_UA_CFF", 1): "Text",
    ("D.MNH.PR.ASAL.GESTIO.GEDMFI000_UA_CFF", 2): "Mixed",
    ("D.MNH.PR.ASAL.GESTIO.GEDMFI000_UA_CFF", 3): "Form",
}

# Hand-adjudicated corrections to Gemini's blocks, applied at build time.
# Shape: { (doc_key, page): { "fields": {label_substr: new_value},
#                             "choice_state": {label_substr: "checked"|"unchecked"},
#                             "drop": [substr,...], "note": "..." } }
# Empty where Claude's high-res review found Gemini already correct (the common case here).
CORRECTIONS = {
    ("D.MNH.PR.ASAL.GESTIO.GEDMFI000_UA_CFF", 2): {
        "fields": {"Téléphone": "3031 (service et appel gratuits)"},
        "note": "Gemini paraphrased the phone annotation; restored verbatim from text layer.",
    },
}


def digits(s):
    return re.sub(r"\D", "", s or "")


def value_grounded(value, tl_nospace, tl_digits, tl):
    v = value.strip()
    if not v:
        return True
    return (re.sub(r"\s+", "", v) in tl_nospace) or (digits(v) and digits(v) in tl_digits) or (v in tl)


def apply_corrections(doc, page, blocks):
    fix = CORRECTIONS.get((doc, page))
    if not fix:
        return blocks
    out = []
    for b in blocks:
        b = dict(b)
        if b["type"] == "field":
            for sub, val in fix.get("fields", {}).items():
                if sub.lower() in (b.get("field_label") or "").lower():
                    b["field_value"] = val
        if b["type"] == "choice":
            for sub, st in fix.get("choice_state", {}).items():
                if sub.lower() in (b.get("choice_label") or "").lower():
                    b["choice_state"] = st
        if any(sub.lower() in (b.get("content") or "").lower() for sub in fix.get("drop", [])):
            continue
        out.append(b)
    return out


def block_md(b):
    t = b["type"]
    content = (b.get("content") or "").strip()
    if t == "heading":
        return f"### {content}" if content else ""
    if t == "field":
        lbl = (b.get("field_label") or "").strip()
        val = (b.get("field_value") or "").strip()
        if not lbl and not val:
            return content
        return f"- **{lbl or '(field)'}:** {val if val else '_(blank)_'}"
    if t == "choice":
        lbl = (b.get("choice_label") or "").strip()
        mark = "x" if (b.get("choice_state") or "").lower() == "checked" else " "
        return f"- [{mark}] {lbl}" if lbl else content
    if t == "table":
        return content
    if t == "figure":
        kind = b.get("figure_kind", "figure")
        return f"_[{kind}] {content}_" if content else ""
    return content  # text, marginalia, other


def main():
    pdfs = discover_pdfs()
    gem = {(r["doc"], r["page"]): r for r in json.load(open(GEMINI_EXTRACT))}
    os.makedirs("results", exist_ok=True)
    os.makedirs("ground_truth", exist_ok=True)

    gt_records = []
    key_pages = []
    ungrounded = []
    doc_cache = {}
    for (doc, page), r in sorted(gem.items()):
        if doc not in doc_cache:
            doc_cache[doc] = fitz.open(pdfs[doc])
        tl = doc_cache[doc][page - 1].get_text()
        tl_nospace = re.sub(r"\s+", "", tl)
        tl_digits = digits(tl)

        blocks = apply_corrections(doc, page, r.get("blocks", []))
        for b in blocks:
            if b["type"] == "field" and (b.get("field_value") or "").strip():
                if not value_grounded(b["field_value"], tl_nospace, tl_digits, tl):
                    ungrounded.append((doc, page, b.get("field_label", ""), b["field_value"]))

        cat = PAGE_CATEGORIES.get((doc, page), "?")
        lines = [block_md(b) for b in blocks]
        md = "\n".join(l for l in lines if l and l.strip()).strip()
        gt_records.append({"doc": doc, "page": page, "category": cat, "md": md})
        key_pages.append({"doc": doc, "page": page, "label": cat})

    gt_records.sort(key=lambda r: (r["doc"], r["page"]))
    json.dump(gt_records, open("results/_gt_markdown.json", "w"), indent=2, ensure_ascii=False)
    json.dump({"taxonomy": ["Text", "Form", "Table", "Mixed"], "pages": key_pages},
              open("ground_truth/answer_key.json", "w"), indent=2, ensure_ascii=False)

    L = ["# GROUND TRUTH — insurance corpus (vision multi-source: Gemini 3.5 Flash + "
         "text layer + Claude hi-res adjudication)\n"]
    for r in gt_records:
        L.append(f"\n\n---\n\n## {short_label(r['doc'])} — page {r['page']}  "
                 f"[category: {r['category']}]\n")
        L.append(r["md"] or "*(empty)*")
    open("ground_truth/GROUND_TRUTH.md", "w").write("\n".join(L) + "\n")

    print(f"GT built: {len(gt_records)} pages -> results/_gt_markdown.json + "
          f"ground_truth/GROUND_TRUTH.md")
    print(f"answer_key.json categories: "
          f"{ {r['label']: sum(1 for x in key_pages if x['label']==r['label']) for r in key_pages} }")
    if ungrounded:
        print(f"\n[!] {len(ungrounded)} field value(s) NOT grounded in text layer (review):")
        for doc, page, lbl, val in ungrounded:
            print(f"    {short_label(doc)} p{page}: {lbl[:30]!r} = {val!r}")
    else:
        print("All field values grounded in the text layer.")


if __name__ == "__main__":
    main()
