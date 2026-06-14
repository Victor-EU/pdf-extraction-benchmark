#!/usr/bin/env python3
"""Gemini native-PDF (file) vs rendered-image (image) A/B report.

Isolates the INPUT-METHOD effect within each Gemini model, holding model+prompt+schema fixed:
  - objective dims (content/numbers/tables/order) from results/_extraction_objective.json
  - figure dims (graph-data/diagram-structure) from results/_gemini_modes_judging.json
    (a dedicated 4-way BLIND judge over the 4 Gemini configs — separate from the canonical 8-way)
  - cost from the raw per-page extract caches

Writes results/GEMINI_FILE_MODE.md.
"""
import json
from collections import defaultdict

CONFIGS = [  # (objective key, label, model, mode, raw extract json)
    ("gemini_flash",           "Gemini 3.5 Flash · image", "flash", "image",
     "results/_gemini_gemini_flash_extract.json"),
    ("gemini_flash_file",      "Gemini 3.5 Flash · file",  "flash", "file",
     "results/_gemini_gemini_flash_file_extract.json"),
    ("gemini_flash_lite",      "Gemini 3.1 Flash-Lite · image", "lite", "image",
     "results/_gemini_gemini_flash_lite_extract.json"),
    ("gemini_flash_lite_file", "Gemini 3.1 Flash-Lite · file",  "lite", "file",
     "results/_gemini_gemini_flash_lite_file_extract.json"),
]


def pct(x):
    return f"{100*x:.0f}%" if x is not None else "–"


def signed(a, b):
    if a is None or b is None:
        return "–"
    d = 100 * (b - a)
    if abs(d) < 0.5:
        return "±0pp"
    return f"{d:+.0f}pp"


def fig_means(judging_path):
    """mean graph/diagram fidelity per config over pages where a graph/diagram exists."""
    fig = json.load(open(judging_path))
    g = defaultdict(list); d = defaultdict(list)
    ng = nd = 0
    for r in fig:
        if r.get("error"):
            continue
        hg, hd = bool(r.get("graphs")), bool(r.get("diagrams"))
        ng += hg; nd += hd
        for vd, s in r.get("scores", {}).items():
            if hg and s.get("graph_score") is not None:
                g[vd].append(s["graph_score"])
            if hd and s.get("diagram_score") is not None:
                d[vd].append(s["diagram_score"])
    mean = lambda xs: sum(xs) / len(xs) / 100 if xs else None
    return {k: mean(v) for k, v in g.items()}, {k: mean(v) for k, v in d.items()}, ng, nd


def cost_and_health(raw_path):
    data = json.load(open(raw_path))
    cost = sum(r.get("cost_usd", 0) for r in data)
    intok = sum(r.get("in_tok", 0) for r in data)
    outok = sum(r.get("out_tok", 0) for r in data)
    secs = [r["seconds"] for r in data if r.get("seconds")]
    bad = [(r["doc"], r["page"]) for r in data
           if r.get("error") or r.get("status") == "incomplete"]
    return cost, intok, outok, (sum(secs) / len(secs) if secs else 0), bad


def main():
    obj = json.load(open("results/_extraction_objective.json"))
    gmean, dmean, ng, nd = fig_means("results/_gemini_modes_judging.json")

    rows = {}
    for key, label, model, mode, raw in CONFIGS:
        o = obj[key]["overall"]
        cost, it, ot, sec, bad = cost_and_health(raw)
        rows[key] = {"label": label, "model": model, "mode": mode,
                     "content": o["recall"], "numbers": o["nrec"],
                     "tables": o["table_presence"], "order": o["tau"],
                     "graph": gmean.get(key), "diagram": dmean.get(key),
                     "cost": cost, "in": it, "out": ot, "sec": sec, "bad": bad}

    L = []
    w = L.append
    w("# Gemini native-PDF (`file`) vs rendered-image (`image`) — does the free text layer help?")
    w("")
    w("Same model, same prompt, same block schema, `thinkingLevel=minimal` — only the INPUT changes: "
      "a rendered **PNG** (`image`) vs the native **1-page PDF** (`file`, from which Gemini 3.x extracts "
      "the embedded text layer *and does not bill those tokens*). The gpt-5 study found `file` wins on "
      "clean text but over-calls Text on Mixed pages and loses on figures — does Gemini behave the same?")
    w("")
    w(f"Figure dims = a dedicated BLIND 4-way gpt-5 vision judge over these 4 configs only "
      f"({ng} graph pages, {nd} diagram pages), separate from the canonical 8-vendor judge so those "
      f"numbers are NOT directly comparable to the main matrix — read the image↔file DELTA, not the level.")
    w("")
    w("> _Re-judged 2026-06-13 at no-truncation figure caps (`AUDIT_VEND_CAP.md`). Clipping here was mild "
      "and balanced image↔file (flash 18 vs 15 figures clipped; lite 1 vs 0; blob never exceeded 7000), so "
      "the verdict is unchanged — confirmed not a truncation artifact._")
    w("")
    w("## The A/B matrix")
    w("")
    w("| Config | Content | Numbers | Tables | Graph data | Diagram | Order τ | Cost (599pp) |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|")
    for key, *_ in CONFIGS:
        r = rows[key]
        w(f"| {r['label']} | {pct(r['content'])} | {pct(r['numbers'])} | {pct(r['tables'])} | "
          f"{pct(r['graph'])} | {pct(r['diagram'])} | {pct(r['order'])} | ${r['cost']:.2f} |")
    w("")
    w("## File − image delta (per model)")
    w("")
    w("| Model | ΔContent | ΔNumbers | ΔTables | ΔGraph | ΔDiagram | ΔCost |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    for model, ik, fk in [("Gemini 3.5 Flash", "gemini_flash", "gemini_flash_file"),
                          ("Gemini 3.1 Flash-Lite", "gemini_flash_lite", "gemini_flash_lite_file")]:
        i, f = rows[ik], rows[fk]
        dcost = f["cost"] - i["cost"]
        w(f"| {model} | {signed(i['content'], f['content'])} | {signed(i['numbers'], f['numbers'])} | "
          f"{signed(i['tables'], f['tables'])} | {signed(i['graph'], f['graph'])} | "
          f"{signed(i['diagram'], f['diagram'])} | {dcost:+.2f} |")
    w("")
    w("## Token economics (the free-native-text claim)")
    w("")
    w("| Config | mean in-tok/pg | mean out-tok/pg | mean s/pg |")
    w("|---|---:|---:|---:|")
    for key, *_ in CONFIGS:
        r = rows[key]
        w(f"| {r['label']} | {r['in']//599} | {r['out']//599} | {r['sec']:.2f} |")
    w("")
    w("## Verdict")
    w("")
    w("**Native-PDF input is a wash for Gemini — keep `image` mode as canonical.** Every quality "
      "dimension lands within ±1–2pp of rendered-image input (noise): Flash is effectively identical "
      "(graph +1 / diagram −2), Flash-Lite is marginally *worse* in `file` (numbers −1, graph −2, order "
      "−2) and added 2 more degenerate pages. This is the OPPOSITE of the gpt-5 image-vs-file split, "
      "where the text layer measurably helped clean text — here Gemini's native vision already saturates "
      "text/number recall (~96–97%) on born-digital PDFs, so the embedded text layer has nothing to add.")
    w("")
    w("**The free-native-text claim is real but doesn't move cost.** `file` cuts input ~38% (1446→891 "
      "tok/pg) and is ~15% faster, but output tokens (~1000/pg, *unchanged*) dominate the bill at "
      "output-rate ≫ input-rate — so Flash saves only $0.77 (11%) and Flash-Lite $0.07 (6%). Native PDF "
      "is worth choosing only at high volume, and only for Flash (Flash-Lite `file` is slightly worse and "
      "flakier). For this benchmark the canonical 8-vendor matrix stays on `image` mode.")
    w("")
    bad_lines = []
    for key, *_ in CONFIGS:
        for doc, page in rows[key]["bad"]:
            bad_lines.append(f"  - {rows[key]['label']}: {doc} p{page} (degenerate/empty)")
    if bad_lines:
        w("## Degenerate pages")
        w("")
        w("\n".join(bad_lines))
        w("")
    open("results/GEMINI_FILE_MODE.md", "w").write("\n".join(L) + "\n")
    print("wrote results/GEMINI_FILE_MODE.md\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
