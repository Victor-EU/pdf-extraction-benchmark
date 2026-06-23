#!/usr/bin/env python3
"""Corpus discovery — the single source of truth for which PDFs the benchmark runs on.

Every script that needs the document list imports from here instead of hardcoding doc
names or globbing `Data/*.pdf` inline. Two reasons this exists:
  1. `glob("Data/*.pdf")` is CASE-SENSITIVE on macOS, so a file saved as `.PDF` is
     silently dropped (it happened: 1 of 2 insurance PDFs went missing). `discover_pdfs`
     matches both cases.
  2. The corpus is now auto-discovered, not a hardcoded {Alpha/IAR/SOTER} dict — drop
     your PDFs in Data/ and the whole pipeline picks them up.

A "doc key" is the filename without extension (what the render manifest and every
`_extract_*.json` keys on). `short_label` gives a human-friendly name for reports.
"""
import os
import glob as _glob


def discover_pdfs(data_dir="Data"):
    """{doc_key: path} for every *.pdf / *.PDF in data_dir (case-insensitive, deduped)."""
    seen = {}
    for pat in ("*.pdf", "*.PDF"):
        for p in _glob.glob(os.path.join(data_dir, pat)):
            key = os.path.splitext(os.path.basename(p))[0]
            seen.setdefault(key, p)
    return dict(sorted(seen.items()))


def doc_keys(data_dir="Data"):
    return list(discover_pdfs(data_dir).keys())


def short_label(doc_key, maxlen=22):
    """A compact, report-friendly label. Insurance filenames are long and noisy
    (`AE_33369592200463_17082__LAYOUNI_Fadhel__...`); collapse to the first informative
    token(s). Falls back to a truncation for unknown shapes."""
    base = doc_key.replace("__", "_")
    head = base.split("_")[0]
    # Known prefixes in this corpus -> friendly names
    KNOWN = {
        "AE": "Attestation-emp",
        "D.MNH.PR.ASAL.GESTIO.GEDMFI000": "MNH-aide-sociale",
    }
    for pref, lbl in KNOWN.items():
        if doc_key.startswith(pref):
            return lbl
    return (head if len(head) <= maxlen else head[:maxlen]).strip("_")


if __name__ == "__main__":
    for k, p in discover_pdfs().items():
        print(f"{short_label(k):<20} {k}  ->  {p}")
