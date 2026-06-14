#!/usr/bin/env python3
"""Automated GT error DETECTOR via the born-digital text layer.

For every page, compare the set of printed NUMERIC tokens in the PDF text layer (exact,
ground-truth for anything printed) against the numbers in the GROUND_TRUTH markdown page.
A printed number ABSENT from the GT ("missing_printed") is a faithful-transcription defect:
the GT either dropped it or replaced it with a hallucinated value. No vision needed; runs on
all 599 pages, so it scopes the chart-data problem corpus-wide and yields a rebuild worklist.

GT's legitimate ~estimates of LABEL-FREE chart points show up only as 'extra_gt' (GT numbers
not in the text layer), NOT as missing_printed — so ranking by missing_printed is robust to
honest estimation and isolates dropped/changed PRINTED data.

Env: GT_MD (default results/_gt_markdown.json), OUT (default results/gt_audit_v2/textlayer_diff.json)
"""
import fitz, json, os, re, glob, collections

# Digit run with at most one decimal/thousands separator BETWEEN digits — does NOT span
# spaces or commas-with-spaces, so "185, 184, 165" -> three tokens, not one mega-token
# (the earlier tokenizer bug that made comma-separated chart series falsely look 'missing').
NUM = re.compile(r"\d+(?:[.,]\d+)*")

def norm_tokens(text):
    """Counter of normalized numeric tokens (>=2 significant digits), separators stripped."""
    out = collections.Counter()
    for m in NUM.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if len(digits) >= 2:
            out[digits] += 1
    return out

def main():
    key = json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))
    labels = {(p["doc"], p["page"]): p["final_label"] for p in key["pages"]}
    gt_path = os.environ.get("GT_MD", "results/_gt_markdown.json")
    gt = {(r["doc"], r["page"]): r.get("md", "") for r in json.load(open(gt_path))}
    print(f"GT source: {gt_path}")
    pdfs = {os.path.splitext(os.path.basename(p))[0]: p for p in glob.glob("Data/*.pdf")}

    rows = []
    for doc, path in pdfs.items():
        d = fitz.open(path)
        for i in range(len(d)):
            page = i + 1
            tl = norm_tokens(d[i].get_text())
            g = norm_tokens(gt.get((doc, page), ""))
            missing = tl - g
            extra = g - tl
            tl_n = sum(tl.values()); miss_n = sum(missing.values())
            rows.append({
                "doc": doc, "page": page, "label": labels.get((doc, page), "?"),
                "tl_count": tl_n, "missing_printed": miss_n,
                "missing_ratio": round(miss_n / tl_n, 3) if tl_n else 0.0,
                "extra_gt": sum(extra.values()),
                "missing_tokens": sorted(missing.elements())[:40],
            })
        d.close()

    os.makedirs("results/gt_audit_v2", exist_ok=True)
    out_path = os.environ.get("OUT", "results/gt_audit_v2/textlayer_diff.json")
    json.dump(rows, open(out_path, "w"), indent=1)

    by_label = collections.defaultdict(lambda: [0, 0, 0])
    for r in rows:
        b = by_label[r["label"]]; b[0]+=1; b[1]+=r["tl_count"]; b[2]+=r["missing_printed"]
    print(f"{len(rows)} pages. Printed-number recall by category (1 - missing/printed):")
    for lab, (n, tl, miss) in sorted(by_label.items(), key=lambda x:-x[1][1]):
        rec = 1 - miss/tl if tl else 1.0
        print(f"  {lab:16} pages={n:3}  printed_nums={tl:5}  missing={miss:4}  recall={rec:.1%}")
    tot_tl = sum(r['tl_count'] for r in rows); tot_miss = sum(r['missing_printed'] for r in rows)
    print(f"  {'TOTAL':16} pages={len(rows):3}  printed_nums={tot_tl:5}  missing={tot_miss:4}  recall={1-tot_miss/tot_tl:.1%}")

    print("\nTop 30 pages by missing printed numbers:")
    for r in sorted(rows, key=lambda r:(-r["missing_printed"], -r["missing_ratio"]))[:30]:
        print(f"  {r['doc'][:26]:26} p{r['page']:>4} {r['label']:14} "
              f"printed={r['tl_count']:3} missing={r['missing_printed']:3} ({r['missing_ratio']:.0%})")

if __name__ == "__main__":
    main()
