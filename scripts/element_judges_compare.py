#!/usr/bin/env python3
"""Cross-family confirmation: per-element-type recall under gpt-5 judge vs Gemini judge.

Both judges scored the SAME fixed GT element inventory (Stage A). If the per-type vendor ranking
reproduces under a non-OpenAI judge, the 'who is good at what' conclusions are not a gpt-5-judge
artifact. Output: results/ELEMENT_JUDGES.md
"""
import json
from collections import defaultdict

VEND_LABEL = {
    "gemini_flash": "Gemini 3.5 Flash", "gemini_flash_lite": "Gemini 3.1 Flash-Lite",
    "landingai": "Landing AI", "pymupdf": "PyMuPDF", "llamaparse": "LlamaParse",
    "tesseract": "Tesseract", "gpt5_image": "gpt-5 (image)", "gpt5_file": "gpt-5 (file)",
}
CLEAN = ["gemini_flash", "gemini_flash_lite", "landingai", "pymupdf", "llamaparse", "tesseract"]
TYPE_ORDER = ["data_table", "chart", "diagram", "kpi_callout", "narrative_text",
              "title_heading", "footnote_source"]
TYPE_LABEL = {"data_table": "Data tables", "chart": "Charts", "diagram": "Diagrams",
              "kpi_callout": "KPI callouts", "narrative_text": "Narrative", "title_heading": "Titles",
              "footnote_source": "Chrome"}


def agg(judg_path, elems):
    judg = json.load(open(judg_path))
    R = defaultdict(lambda: defaultdict(float)); S = defaultdict(lambda: defaultdict(float))
    for pg in judg:
        if pg.get("error"): continue
        for s in pg.get("scores", []):
            meta = elems.get((pg["doc"], pg["page"], s["id"]))
            if not meta: continue
            typ, sal = meta
            for vd, sc in s["vendors"].items():
                if sc.get("recall") is None: continue
                R[typ][vd] += sc["recall"]*sal; S[typ][vd] += sal
    return {t: {v: (R[t][v]/S[t][v] if S[t][v] else None) for v in VEND_LABEL} for t in TYPE_ORDER}


def main():
    elems = {}
    for r in json.load(open("results/_gt_elements.json")):
        for e in r["elements"]:
            elems[(r["doc"], r["page"], e["id"])] = (e["type"], e.get("salience", 3))
    g5 = agg("results/_element_judging.json", elems)
    gm = agg("results/_element_judging_gemini.json", elems)

    def p(x): return f"{x:.0f}" if x is not None else "–"
    def winner(d, t):
        cr = sorted([(d[t][v], v) for v in CLEAN if d[t][v] is not None], reverse=True)
        return cr[0][1] if cr else None

    L = []; w = L.append
    w("# Element-type leaderboard — gpt-5 judge vs cross-family Gemini judge")
    w("")
    w("Same vendor extractions, same fixed GT element inventory (Stage A), same blind shuffle. Only the "
      "judge model family differs. Agreement on the per-type winner rules out judge-family bias.")
    w("")
    w("| Element type | gpt-5 winner | Gemini winner | agree? |")
    w("|---|---|---|:--:|")
    for t in TYPE_ORDER:
        a, b = winner(g5, t), winner(gm, t)
        w(f"| {TYPE_LABEL[t]} | {VEND_LABEL.get(a,'–')} | {VEND_LABEL.get(b,'–')} | "
          f"{'✓' if a==b else '✗'} |")
    w("")
    for t in TYPE_ORDER:
        w(f"## {TYPE_LABEL[t]} — recall by judge")
        w("")
        w("| Vendor | gpt-5 judge | Gemini judge | Δ |")
        w("|---|---:|---:|---:|")
        ranked = sorted(VEND_LABEL, key=lambda v: -(g5[t][v] or -1))
        for v in ranked:
            a, b = g5[t][v], gm[t][v]
            d = f"{b-a:+.0f}" if (a is not None and b is not None) else "–"
            w(f"| {VEND_LABEL[v]} | {p(a)} | {p(b)} | {d} |")
        w("")
    open("results/ELEMENT_JUDGES.md", "w").write("\n".join(L)+"\n")
    print("wrote results/ELEMENT_JUDGES.md")
    print("\n".join(L[:18]))


if __name__ == "__main__":
    main()
