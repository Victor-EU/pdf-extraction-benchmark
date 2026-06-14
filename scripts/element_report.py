#!/usr/bin/env python3
"""Aggregate the element-level judging into a 'who is good at what' report.

Joins Stage A (results/_gt_elements.json: type+salience per element) with Stage B
(results/_element_judging.json: per-element per-vendor recall+wrong). For each ELEMENT TYPE,
across all 599 pages, computes per vendor:
  - recall  = salience-weighted mean recall (how much of that element type's info is conveyed)
  - fidelity= salience-weighted mean (100-wrong) (how little it invents/contradicts)
  - coverage= % of elements of that type captured at all (recall >= 50)
  - n       = element count (sample size)
Element TYPE is intrinsic, so a chart is judged as a chart whether on a deck or annual report —
removing the page-bucket/document confound of the category table.

Output: results/ELEMENT_AUDIT.md  (+ results/_element_agg.json for downstream)
"""
import json
from collections import defaultdict

VEND_LABEL = {
    "gemini_flash": "Gemini 3.5 Flash", "gemini_flash_lite": "Gemini 3.1 Flash-Lite",
    "landingai": "Landing AI", "pymupdf": "PyMuPDF", "llamaparse": "LlamaParse",
    "tesseract": "Tesseract", "gpt5_image": "gpt-5 (image) ◆", "gpt5_file": "gpt-5 (file) ◆",
}
CLEAN = ["gemini_flash", "gemini_flash_lite", "landingai", "pymupdf", "llamaparse", "tesseract"]
ALL = CLEAN + ["gpt5_image", "gpt5_file"]
TYPE_ORDER = ["data_table", "chart", "diagram", "kpi_callout", "narrative_text",
              "title_heading", "footnote_source"]
TYPE_LABEL = {
    "data_table": "Data tables", "chart": "Charts/graphs (with data)", "diagram": "Diagrams/flows/maps",
    "kpi_callout": "KPI / metric callouts", "narrative_text": "Narrative prose & bullets",
    "title_heading": "Titles & headings", "footnote_source": "Footnotes / sources / logos (chrome)",
}
DOC_SHORT = {"IAR_FY25_EN": "AnnualRpt", "20190308_Projet_Alpha_Restitution": "Alpha-deck",
             "SOTER - Company Presentation - vFF": "SOTER-deck"}

# Static analysis narrative appended after the generated tables. Kept here (not hand-appended to the
# .md) so regenerating the report never silently wipes it. The CI / truncation figures describe a fixed
# result; full reproducible trail in AUDIT_VEND_CAP.md.
FOOTER = [
"",
"---",
"",
"## Truncation correction (2026-06-13)",
"",
"These numbers are the **corrected, no-truncation run**. The original judge truncated each vendor's "
"per-page text at 6,000 chars (`VEND_CAP`), which clipped only Landing AI on 145 pages (24% — its output "
"is 2× longer and its figure prose sits at the page end). Re-judging at a 16,000-char cap (zero truncation) "
"raised Landing AI's KPI 84→98, charts 77→85, diagrams 85→89, tables 91→93; every other vendor moved ≤1 "
"point and **no ranking changed**. Full trail: `AUDIT_VEND_CAP.md`.",
"",
"## Significance — bootstrap 95% CI on the clean winner's lead",
"",
"Charts **+3.8 [+2.1,+5.6]**, diagrams **+3.4 [+0.4,+6.8]**, prose **+0.8 [+0.4,+1.2]**, titles "
"**+0.8 [+0.3,+1.3]**, chrome **+2.5 [+1.4,+3.6]** are real wins for Gemini Flash. **Tables +0.2 "
"[−0.5,+0.9]** and **KPI +0.4 [0.0,+1.0]** are statistical **ties** — report them as ties, not wins.",
"",
"## Hand-audit of the scores (vs GT) — are these numbers real?",
"",
"The highest-divergence elements per data type were read by hand (GT element key_facts vs each vendor's "
"actual page text, against the page image). The scores are faithful, with one documented judge limitation:",
"",
"- **Data tables — faithful.** On born-digital tables PyMuPDF reproduces every value exactly from the text "
"layer (recall 100); Tesseract scores recall ~30 with *wrong ~70* — it emits genuinely wrong numbers, "
"matching its low table fidelity. The PyMuPDF–Landing AI table gap (93 vs 93) is a tie.",
"- **Charts — faithful, mechanism = text layer.** PyMuPDF earns chart credit because born-digital decks "
"carry the data labels in the text layer (verified on SOTER quarterly-EBITDA values). It captures chart "
"NUMBERS, not chart geometry.",
"- **Diagrams — faithful at the extremes, one caveat (verified vs page image).** Visual-only diagrams "
"(e.g. IAR p139 six-domain security graphic, labels rendered inside the image) → PyMuPDF recall 0, "
"correctly (labels absent from its text layer; confirmed against the rendered page). Text-dense org "
"charts (SOTER p92) → PyMuPDF recall 100 even though the *reporting structure is scrambled* into floating "
"tokens. The paraphrase-tolerant judge under-penalizes lost diagram STRUCTURE when all tokens are "
"present, so PyMuPDF's true diagram score is if anything **below** the reported 50% — i.e. the "
"vision-model lead on diagrams is conservative, never inflated.",
"",
"## Cross-family confirmation (gpt-5 judge vs Gemini judge)",
"",
"The same fixed element inventory was re-scored by a non-OpenAI judge (gemini-3.5-flash, $15.81), also at "
"the corrected 16,000-char cap. Per-type winners agree 5/7. The two that differ — **diagrams** (gpt-5 → "
"Gemini Flash 92; Gemini judge → Landing AI 95) and **KPIs** (Gemini Flash / Landing AI / PyMuPDF all "
"98–100) — are **ties at the top of the vision tier**, not rank reversals: both judges put the figure-reading "
"tier (Gemini/gpt-5/Landing AI/**LlamaParse agentic**, ~83–95) far above the *pure text-layer* parsers "
"(PyMuPDF, Tesseract ~45–50) on diagrams, and both rank Gemini Flash #1 on tables, "
"charts, narrative, titles and chrome. The Gemini judge is uniformly more lenient (Tesseract tables +15, "
"chrome +14) without reordering the strong tier. Full table: `results/ELEMENT_JUDGES.md`.",
"",
"## LlamaParse tier correction (2026-06-13) — these numbers are AGENTIC tier",
"",
"LlamaParse is scored here at its **`agentic` tier (its most capable mode)**, re-run after we found the "
"original benchmark had used the middle `accurate` tier, which silently dropped whole born-digital pages. "
"Switching to agentic lifts LlamaParse on every element type — **charts 56→83, diagrams 46→83, tables "
"79→97, footnotes/sources 61→87, prose 84→100** (gpt-5 judge) — moving it from a text-layer specialist to "
"a top-tier all-rounder (element-ALL 78→95). Agentic runs an LVM loop, so unlike PyMuPDF/Tesseract it "
"actually *reads* charts and diagrams. Every other vendor moved ≤0.3 pp on the re-judge. Full trail: "
"`AUDIT_LLAMAPARSE_MODE.md`.",
]


def load():
    elems = {}
    for r in json.load(open("results/_gt_elements.json")):
        for e in r["elements"]:
            elems[(r["doc"], r["page"], e["id"])] = (e["type"], e.get("salience", 3), r["doc"])
    judg = json.load(open("results/_element_judging.json"))
    return elems, judg


def main():
    elems, judg = load()
    # type -> vend -> [recall*sal sum, sal sum, fidelity*sal sum, captured count, count]
    R = defaultdict(lambda: defaultdict(float)); S = defaultdict(lambda: defaultdict(float))
    F = defaultdict(lambda: defaultdict(float))
    CAP = defaultdict(lambda: defaultdict(int)); N = defaultdict(lambda: defaultdict(int))
    # type x doc recall (salience-weighted) for confound check
    DR = defaultdict(lambda: defaultdict(float)); DS = defaultdict(lambda: defaultdict(float))
    rows = []  # divergence

    for pg in judg:
        if pg.get("error"): continue
        for s in pg.get("scores", []):
            meta = elems.get((pg["doc"], pg["page"], s["id"]))
            if not meta: continue
            typ, sal, doc = meta
            recs = {}
            for vd, sc in s["vendors"].items():
                rec = sc.get("recall"); wr = sc.get("wrong", 0)
                if rec is None: continue
                recs[vd] = rec
                R[typ][vd] += rec*sal; S[typ][vd] += sal
                F[typ][vd] += (100-wr)*sal
                if rec >= 50: CAP[typ][vd] += 1
                N[typ][vd] += 1
                DR[(typ, doc)][vd] += rec*sal; DS[(typ, doc)][vd] += sal
            cr = [recs[v] for v in CLEAN if v in recs]
            if len(cr) >= 2:
                rows.append((typ, max(cr)-min(cr), sal, pg["doc"], pg["page"], s["id"], recs))

    def rec(t, v): return R[t][v]/S[t][v] if S[t][v] else None
    def fid(t, v): return F[t][v]/S[t][v] if S[t][v] else None
    def cov(t, v): return 100*CAP[t][v]/N[t][v] if N[t][v] else None
    def p(x): return f"{x:.0f}%" if x is not None else "–"

    L = []; w = L.append
    w("# Element-level audit — which vendor is good at what (v2 GT)")
    w("")
    w("Every page's ground truth was decomposed into typed content elements (Stage A); each vendor was "
      "then graded **element by element** (Stage B, blind). Scores are aggregated BY ELEMENT TYPE across "
      "all 599 pages and salience-weighted, so a chart is judged as a chart wherever it appears — no page-"
      "bucket or document confound. gpt-5 rows (◆) are upper bounds (built the GT).")
    w("")
    w("**recall** = % of that element's information conveyed · **fidelity** = 100−invented/contradicted · "
      "**coverage** = % of those elements captured at all (recall≥50) · **n** = element count.")
    w("")
    # element counts
    counts = {t: max(N[t][v] for v in ALL) for t in TYPE_ORDER}
    w("**Elements per type (n):** " + ", ".join(f"{TYPE_LABEL[t]} {counts[t]}" for t in TYPE_ORDER))
    w("")

    # headline: per-type clean winner
    w("## Headline — best clean vendor per element type")
    w("")
    w("| Element type | n | Winner (clean) | recall | Runner-up | gap |")
    w("|---|---:|---|---:|---|---:|")
    for t in TYPE_ORDER:
        cr = sorted([(rec(t, v), v) for v in CLEAN if rec(t, v) is not None], reverse=True)
        if len(cr) < 2: continue
        gap = cr[0][0]-cr[1][0]
        w(f"| {TYPE_LABEL[t]} | {counts[t]} | **{VEND_LABEL[cr[0][1]]}** | {p(cr[0][0])} | "
          f"{VEND_LABEL[cr[1][1]]} | +{gap:.0f} |")
    w("")

    # full per-type tables
    for t in TYPE_ORDER:
        w(f"## {TYPE_LABEL[t]}  (n={counts[t]})")
        w("")
        w("| Vendor | recall | fidelity | coverage |")
        w("|---|---:|---:|---:|")
        ranked = sorted(ALL, key=lambda v: -(rec(t, v) or -1))
        for v in ranked:
            w(f"| {VEND_LABEL[v]} | {p(rec(t,v))} | {p(fid(t,v))} | {p(cov(t,v))} |")
        # doc cross-tab (recall)
        docs = sorted({d for (tt, d) in DR if tt == t}, key=lambda d: DOC_SHORT.get(d, d))
        if len(docs) > 1:
            w("")
            w("_recall by document:_ " + " · ".join(
                f"{DOC_SHORT.get(d,d)}: " + ", ".join(
                    f"{v.split('_')[0][:4]} {DR[(t,d)][v]/DS[(t,d)][v]:.0f}%" for v in
                    sorted(CLEAN, key=lambda v:-(DR[(t,d)][v]/DS[(t,d)][v] if DS[(t,d)][v] else 0))[:3]
                    if DS[(t,d)][v]) for d in docs))
        w("")

    # per-vendor strengths/weaknesses
    w("## Per-vendor profile (clean recall by type)")
    w("")
    w("| Vendor | " + " | ".join(TYPE_LABEL[t].split(" (")[0].split("/")[0].strip() for t in TYPE_ORDER) + " |")
    w("|---|" + "---:|"*len(TYPE_ORDER))
    for v in ALL:
        w(f"| {VEND_LABEL[v]} | " + " | ".join(p(rec(t, v)) for t in TYPE_ORDER) + " |")
    w("")

    # --- static analysis footer (kept in-script so it survives regeneration) ---
    for line in FOOTER:
        w(line)

    open("results/ELEMENT_AUDIT.md", "w").write("\n".join(L)+"\n")

    # divergence worklist for hand-audit
    by_t = defaultdict(list)
    for typ, spread, sal, doc, page, eid, recs in rows:
        by_t[typ].append((spread, sal, doc, page, eid, recs))
    wl = {}
    for t in ["data_table", "chart", "diagram", "kpi_callout"]:
        top = sorted(by_t[t], reverse=True)[:8]
        wl[t] = [(d, pg, eid) for _, _, d, pg, eid, _ in top]
    json.dump(wl, open("results/_element_worklist.json", "w"), indent=1)
    agg = {t: {v: {"recall": rec(t, v), "fidelity": fid(t, v), "coverage": cov(t, v), "n": N[t][v]}
               for v in ALL} for t in TYPE_ORDER}
    json.dump(agg, open("results/_element_agg.json", "w"), indent=1)
    print("wrote results/ELEMENT_AUDIT.md, _element_agg.json, _element_worklist.json")
    print("\n".join(L))


if __name__ == "__main__":
    main()
