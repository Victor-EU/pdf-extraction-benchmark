#!/usr/bin/env python3
"""Score vendor extraction completeness vs the reference, segmented by page category.

Objective dimensions (the figure/graph dimension is judged separately by score_figures.py):
  - content_recall : fraction of reference tokens (text-layer ∪ image-OCR) the vendor captured
                     ANYWHERE in its output (text + tables + figure descriptions). "How much info."
  - content_prec   : fraction of vendor text tokens that are in the reference (transcription noise)
  - numeric_recall : fraction of reference NUMBERS recovered (finance fidelity)
  - order_tau      : Kendall-tau of vendor reading order vs reference reading order (spatial)
  - table_presence : on Table/Mixed pages, did the vendor emit a structured table? (dim-2 capability)

Aggregates overall + by the v3 category label. Usage:
  python3 scripts/score_extraction.py <vendor> [<vendor> ...]
"""
import os, re, sys, json, glob
from collections import defaultdict

_word_re = re.compile(r"[^\W\d_]+", re.UNICODE)
_num_re = re.compile(r"\d[\d.,%/]*")

def words(s): return {w.lower() for w in _word_re.findall(s or "") if len(w) > 1}
def nums(s):
    out = set()
    for m in _num_re.findall(s or ""):
        t = m.rstrip(".,/").replace(" ", "")
        if re.sub(r"[^\d]", "", t): out.add(t)
    return out

def key_cats():
    return {(e["doc"], e["page"]): e["final_label"]
            for e in json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))["pages"]}

def load_ref():
    ref = {}
    for f in glob.glob("ground_truth/extraction_ref/*.json"):
        r = json.load(open(f))
        ref[(r["doc"], r["page"])] = r
    return ref

def kendall_tau(order_a, order_b):
    """order_b = list of indices into a's order; tau over concordant pairs."""
    n = len(order_b)
    if n < 2: return None
    c = d = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (order_b[i] - order_b[j])
            if s == 0: continue
            if s < 0: c += 1
            else: d += 1
    return (c - d) / (c + d) if (c + d) else None

def vendor_all_tokens(r):
    toks = set(r.get("text_tokens", []))
    for t in r.get("tables", []): toks |= words(t)
    for f in r.get("figures", []): toks |= words(f.get("content", ""))
    return toks

def vendor_all_nums(r):
    ns = set(r.get("num_tokens", []))
    for t in r.get("tables", []): ns |= nums(t)
    for f in r.get("figures", []): ns |= nums(f.get("content", ""))
    return ns

def order_score(ref_blocks, vendor_blocks):
    """Match each ref block to its best vendor block by token overlap; tau of matched positions."""
    if len(ref_blocks) < 3 or len(vendor_blocks) < 2: return None
    vtok = [words(b) for b in vendor_blocks]
    matched = []
    for rb in ref_blocks:
        rw = words(rb)
        if not rw: continue
        best, bi = 0.0, None
        for vi, vw in enumerate(vtok):
            if not vw: continue
            ov = len(rw & vw) / len(rw)
            if ov > best: best, bi = ov, vi
        if bi is not None and best >= 0.3: matched.append(bi)
    return kendall_tau(range(len(matched)), matched) if len(matched) >= 3 else None


def score_vendor(vendor, ref, cats):
    data = {(r["doc"], r["page"]): r for r in json.load(open(f"results/_extract_{vendor}.json"))}
    rows = []
    for k, refr in ref.items():
        if k not in data: continue
        v = data[k]
        rt = set(refr["ref_tokens"]); rn = set(refr["ref_numbers"])
        vt = vendor_all_tokens(v); vn = vendor_all_nums(v)
        recall = len(rt & vt) / len(rt) if rt else None
        prec = len(set(v.get("text_tokens", [])) & rt) / len(v.get("text_tokens", [])) \
            if v.get("text_tokens") else None
        nrec = len(rn & vn) / len(rn) if rn else None
        tau = order_score(refr["reading_order"], v.get("ordered_texts", []))
        rows.append({"k": k, "cat": cats.get(k, "?"), "recall": recall, "prec": prec,
                     "nrec": nrec, "tau": tau, "has_table": len(v.get("tables", [])) > 0})
    return rows


def agg(rows, field, filt=None):
    vals = [r[field] for r in rows if r[field] is not None and (filt is None or filt(r))]
    return sum(vals) / len(vals) if vals else None


def main():
    ref = load_ref(); cats = key_cats()
    CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]
    vendors = sys.argv[1:]
    report = {}
    for vd in vendors:
        rows = score_vendor(vd, ref, cats)
        ov = {m: agg(rows, m) for m in ["recall", "prec", "nrec", "tau"]}
        # Table RECOVERY = on pages whose dominant content IS a table (label "Table"),
        # did the vendor emit a structured table? "Mixed" is excluded from the denominator:
        # ~half of Mixed pages are chart+text/infographic with NO table, so requiring one
        # there punishes principled abstention and rewards layout->table over-emission.
        # (See memory: pdf_parsing_test_table_metric_artifact.)
        tab_pages = [r for r in rows if r["cat"] == "Table"]
        ov["table_presence"] = sum(1 for r in tab_pages if r["has_table"]) / len(tab_pages) if tab_pages else None
        legacy = [r for r in rows if r["cat"] in ("Table", "Mixed")]  # old (deflating) metric, kept for audit
        ov["table_presence_legacy"] = sum(1 for r in legacy if r["has_table"]) / len(legacy) if legacy else None
        bycat = {}
        for c in CATS:
            bycat[c] = {m: agg(rows, m, lambda r, c=c: r["cat"] == c) for m in ["recall", "nrec", "tau"]}
        report[vd] = {"overall": ov, "by_cat": bycat, "n": len(rows)}

    # print
    def pct(x): return f"{100*x:.0f}%" if x is not None else "  -"
    print(f"\n{'='*70}\nEXTRACTION COMPLETENESS (objective dims) — by vendor\n{'='*70}")
    print(f"{'vendor':<12} {'content':>8} {'prec':>6} {'numbers':>8} {'order':>7} {'tbl-pres':>9}")
    for vd, R in report.items():
        o = R["overall"]
        print(f"{vd:<12} {pct(o['recall']):>8} {pct(o['prec']):>6} {pct(o['nrec']):>8} "
              f"{pct(o['tau']):>7} {pct(o['table_presence']):>9}")
    print(f"\nCONTENT RECALL by category:")
    print(f"{'vendor':<12} " + " ".join(f"{c.split('/')[0][:5]:>7}" for c in CATS))
    for vd, R in report.items():
        print(f"{vd:<12} " + " ".join(f"{pct(R['by_cat'][c]['recall']):>7}" for c in CATS))
    print(f"\nNUMERIC (finance) RECALL by category:")
    print(f"{'vendor':<12} " + " ".join(f"{c.split('/')[0][:5]:>7}" for c in CATS))
    for vd, R in report.items():
        print(f"{vd:<12} " + " ".join(f"{pct(R['by_cat'][c]['nrec']):>7}" for c in CATS))
    json.dump(report, open("results/_extraction_objective.json", "w"), indent=2)
    print("\n[-> results/_extraction_objective.json]")


if __name__ == "__main__":
    main()
