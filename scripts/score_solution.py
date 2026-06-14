#!/usr/bin/env python3
"""Score a PDF-parsing solution's per-page category predictions vs the answer key.

Usage:
  python3 scripts/score_solution.py <solution.json> [--name NAME]

solution.json: JSON array of {"doc":..., "page":..., "label":...}
  optional per-page "seconds" and "cost_usd" fields -> speed/cost metrics.

Outputs overall accuracy, per-category precision/recall/F1/support, macro-F1,
a confusion matrix, and (if timing/cost present) speed + cost summaries.
Writes a markdown report to results/<name>.md and prints a summary.
"""
import json, sys, os
from collections import defaultdict, Counter

CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]


def load_key(path="ground_truth/reconcile/final_answer_key_v3.json"):
    ak = json.load(open(path))["pages"]
    return {(e["doc"], e["page"]): e["final_label"] for e in ak}


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    sol_path = sys.argv[1]
    name = "solution"
    if "--name" in sys.argv:
        name = sys.argv[sys.argv.index("--name") + 1]
    key_path = "ground_truth/reconcile/final_answer_key_v3.json"  # canonical Layer-1 key (DESIGN.md)
    if "--key" in sys.argv:
        key_path = sys.argv[sys.argv.index("--key") + 1]
    sol = json.load(open(sol_path))
    if isinstance(sol, dict) and "pages" in sol:
        sol = sol["pages"]
    key = load_key(key_path)

    pred = {(r["doc"], r["page"]): r["label"] for r in sol}
    secs = [r["seconds"] for r in sol if r.get("seconds") is not None]
    costs = [r["cost_usd"] for r in sol if r.get("cost_usd") is not None]

    # align
    keys = sorted(key.keys())
    missing = [k for k in keys if k not in pred]
    n = len(keys)
    correct = 0
    confusion = defaultdict(lambda: defaultdict(int))  # true -> pred
    tp = Counter(); fp = Counter(); fn = Counter(); support = Counter()
    for k in keys:
        t = key[k]
        support[t] += 1
        p = pred.get(k)
        if p is None:
            confusion[t]["<missing>"] += 1
            fn[t] += 1
            continue
        confusion[t][p] += 1
        if p == t:
            correct += 1; tp[t] += 1
        else:
            fp[p] += 1; fn[t] += 1

    acc = correct / n
    lines = []
    def out(s=""):
        lines.append(s); print(s)

    out(f"# Scorecard: {name}")
    out(f"\nPages scored: {n}  |  predictions missing: {len(missing)}")
    out(f"\n## Overall accuracy: {correct}/{n} = {100*acc:.1f}%")

    out(f"\n## Accuracy by category (recall) + precision/F1")
    out(f"\n| Category | Support | Recall | Precision | F1 |")
    out(f"|---|---:|---:|---:|---:|")
    f1s = []
    for c in CATS:
        s = support[c]
        if s == 0:
            out(f"| {c} | 0 | - | - | - |"); continue
        rec = tp[c] / s
        prec = tp[c] / (tp[c] + fp[c]) if (tp[c] + fp[c]) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        f1s.append(f1)
        out(f"| {c} | {s} | {100*rec:.0f}% | {100*prec:.0f}% | {100*f1:.0f}% |")
    macro = sum(f1s) / len(f1s) if f1s else 0
    out(f"\nMacro-avg F1 (categories present): {100*macro:.1f}%")

    out(f"\n## Confusion matrix (rows = TRUE, cols = predicted)")
    hdr = "| true \\ pred | " + " | ".join(c.split("/")[0][:5] for c in CATS) + " | miss |"
    out("\n" + hdr)
    out("|---|" + "---:|" * (len(CATS) + 1))
    for t in CATS:
        row = [f"{confusion[t][c]}" for c in CATS] + [f"{confusion[t]['<missing>']}"]
        out(f"| {t} | " + " | ".join(row) + " |")

    if secs:
        out(f"\n## Speed")
        out(f"- pages with timing: {len(secs)}")
        out(f"- mean: {sum(secs)/len(secs):.2f}s/page  | min {min(secs):.2f}s | max {max(secs):.2f}s")
        out(f"- total wall (sum): {sum(secs):.0f}s for {len(secs)} pages")
    if costs:
        out(f"\n## Cost")
        out(f"- total: ${sum(costs):.2f}  | mean ${sum(costs)/len(costs):.4f}/page  | for {len(costs)} pages")

    os.makedirs("results", exist_ok=True)
    with open(f"results/{name}.md", "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\n[report -> results/{name}.md]")


if __name__ == "__main__":
    main()
