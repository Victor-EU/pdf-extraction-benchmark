#!/usr/bin/env python3
"""PROOF-OF-CONCEPT: deterministic, binding-aware extraction scoring (no LLM).

Hypothesis: the reason numeric-set recall over-credits text-dumpers (PyMuPDF/Tesseract)
is that it ignores BINDING. If we score each number TOGETHER WITH the label tokens
adjacent to it, the text-dumpers should collapse toward the LLM structure judge's
ranking, while structure-preservers (Gemini, LandingAI, agentic LlamaParse, gpt-5)
should hold up despite serializing tables/charts very differently.

ATOM = (normalized_number, set(alpha label tokens ON THE SAME LINE)).
  - numeric_recall : GT number present ANYWHERE in vendor (the naive set metric).
  - binding_recall : GT atom (number+label) matched by a vendor atom with the SAME
                     number whose own same-line label set covers >= TAU of GT's labels.
                     This is "did the number survive WITH its row/series label."

Born-digital corpus => numbers are an exact oracle, so a MATCH is certain (high
precision). A MISS is ambiguous (binding destroyed vs serialization we can't parse) —
that asymmetry is the headline finding, measured here, not assumed.

Compares to BOTH judge families' rubrics: structure-aware (canonical
_fair_total_judging.json) and content-presence (_fair_total_judging_content.json).
"""
import os, re, sys, json, unicodedata
from collections import defaultdict
from statistics import mean

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_vendor_md import load_pages as _vendor_pages   # reads _extract_<v>.json, page_md()

TAU = float(os.environ.get("TAU", "0.5"))   # fraction of GT row-label tokens needed adjacent

STOP = set("de la le les des du un une et en au aux pour par sur dans avec the of and "
           "in to a an for on is by with as at or from group total source notes note".split())

_num_re = re.compile(r"\d[\d.,]*")
_alpha_re = re.compile(r"[^\W\d_]{2,}", re.UNICODE)


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def norm_num(m):
    t = m.rstrip(".,").replace(",", "").replace(" ", "")
    return t if re.sub(r"[^\d]", "", t) else None


def labels(line):
    return {fold(w) for w in _alpha_re.findall(line)} - STOP


def page_atoms(text):
    """Return (all_numbers_set, list of (num, frozenset(line_labels)) for labeled atoms)."""
    allnums, atoms = set(), []
    for line in text.splitlines():
        nums = [n for n in (norm_num(m.group()) for m in _num_re.finditer(line)) if n]
        if not nums:
            continue
        allnums |= set(nums)
        L = frozenset(labels(line))
        for n in nums:
            atoms.append((n, L))
    return allnums, atoms


def load_pages(path):
    out = {}
    txt = open(path).read()
    for p in re.split(r"\n## ", txt):
        head = p.split("\n", 1)[0]
        m = re.search(r"(.+?) — page (\d+)\b", head)
        if m:
            out[(m.group(1).strip().lstrip("# "), int(m.group(2)))] = p
    return out


def binding_recall(gt_atoms, v_nums, v_atoms):
    """fraction of GT labeled-atoms whose number survives WITH a covering label set."""
    # index vendor atoms by number -> list of label sets
    by_num = defaultdict(list)
    for n, L in v_atoms:
        by_num[n].append(L)
    gt_labeled = [(n, L) for n, L in gt_atoms if L]
    if not gt_labeled:
        return None
    hit = 0
    for n, Lg in gt_labeled:
        cand = by_num.get(n, [])
        ok = any(len(Lg & Lv) / len(Lg) >= TAU for Lv in cand if Lv)
        if ok:
            hit += 1
    return hit / len(gt_labeled)


def main():
    V = ["gemini_flash", "gpt5_image", "landingai", "llamaparse", "pymupdf", "tesseract"]
    # SAME sources the LLM judge uses: GT from _gt_markdown.json, vendors from _extract_<v>.json.
    # (Reading the pre-concatenated vendor_md/*.md is wrong: LandingAI emits markdown '##'
    #  subheaders inside page bodies, so splitting on '\n## ' truncates its pages.)
    gt = {(r["doc"], r["page"]): r.get("md", "")
          for r in json.load(open("results/_gt_markdown.json"))}
    vmd = {v: _vendor_pages(v) for v in V}
    cats = {(e["doc"], e["page"]): e["final_label"]
            for e in json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))["pages"]}
    js = {(r["doc"], r["page"]): r for r in json.load(open("results/_fair_total_judging.json"))}
    jc = {(r["doc"], r["page"]): r
          for r in json.load(open("results/_fair_total_judging_content.json"))}

    # precompute GT atoms
    gt_at = {k: page_atoms(t) for k, t in gt.items()}

    # per (vendor, page) deterministic metrics + judge scores
    rows = []
    for v in V:
        for k, (gnums, gatoms) in gt_at.items():
            if len(gnums) < 3:
                continue
            vp = vmd[v].get(k, "")
            vn, va = page_atoms(vp)
            nrec = len(gnums & vn) / len(gnums)
            brec = binding_recall(gatoms, vn, va)
            jstruct = js.get(k, {}).get("scores", {}).get(v, {}).get("info_recall")
            jcont = jc.get(k, {}).get("scores", {}).get(v, {}).get("info_recall")
            rows.append({"v": v, "k": k, "cat": cats.get(k, "?"), "nrec": nrec,
                         "brec": brec, "js": jstruct, "jc": jcont})

    def avg(vals):
        vals = [x for x in vals if x is not None]
        return 100 * mean(vals) if vals else None

    def fmt(x):
        return f"{x:>5.0f}" if x is not None else "    -"

    # ---- overall table ----
    print(f"\n{'='*72}\nDETERMINISTIC binding-aware POC  (TAU={TAU}) vs LLM judges\n{'='*72}")
    print(f"{'vendor':<14}{'num_rec':>9}{'bind_rec':>10}{'judge_struct':>14}{'judge_content':>15}")
    for v in V:
        r = [x for x in rows if x["v"] == v]
        print(f"{v:<14}{fmt(avg([x['nrec'] for x in r])):>9}"
              f"{fmt(avg([x['brec'] for x in r])):>10}"
              f"{fmt(avg([x['js'] for x in r])):>14}"
              f"{fmt(avg([x['jc'] for x in r])):>15}")

    # ---- per-category binding vs structure judge (the 'surgical' test) ----
    for cat in ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider"]:
        print(f"\n--- {cat}: num_rec / bind_rec / judge_struct ---")
        for v in V:
            r = [x for x in rows if x["v"] == v and x["cat"] == cat]
            if not r:
                continue
            print(f"  {v:<13}{fmt(avg([x['nrec'] for x in r]))} /{fmt(avg([x['brec'] for x in r]))}"
                  f" /{fmt(avg([x['js'] for x in r]))}")

    # ---- correlation: does bind_rec track structure judge MORE than content judge? ----
    def pearson(xs, ys):
        pairs = [(a, b) for a, b in zip(xs, ys) if a is not None and b is not None]
        if len(pairs) < 10:
            return None
        ax, ay = mean(p[0] for p in pairs), mean(p[1] for p in pairs)
        num = sum((a-ax)*(b-ay) for a, b in pairs)
        den = (sum((a-ax)**2 for a, _ in pairs) * sum((b-ay)**2 for _, b in pairs)) ** .5
        return num/den if den else None

    print(f"\n{'='*72}\nPER-PAGE correlation of deterministic vs judge (all vendors pooled)\n{'='*72}")
    nrec = [x["nrec"] for x in rows]; brec = [x["brec"] for x in rows]
    jstr = [x["js"]/100 if x["js"] is not None else None for x in rows]
    jcon = [x["jc"]/100 if x["jc"] is not None else None for x in rows]
    print(f"  numeric_recall  vs structure judge : r = {pearson(nrec, jstr):.3f}")
    print(f"  binding_recall  vs structure judge : r = {pearson(brec, jstr):.3f}")
    print(f"  numeric_recall  vs content   judge : r = {pearson(nrec, jcon):.3f}")
    print(f"  binding_recall  vs content   judge : r = {pearson(brec, jcon):.3f}")

    # ---- disagreement flags: where deterministic and structure judge diverge most ----
    flagged = [x for x in rows if x["brec"] is not None and x["js"] is not None]
    for x in flagged:
        x["gap"] = x["brec"]*100 - x["js"]
    flagged.sort(key=lambda x: abs(x["gap"]), reverse=True)
    print(f"\n{'='*72}\nTOP 12 judge-vs-deterministic DISAGREEMENTS (|bind_rec - judge_struct|)\n{'='*72}")
    print(f"{'vendor':<13}{'doc/page':<42}{'cat':<14}{'bind':>5}{'judge':>6}{'gap':>6}")
    for x in flagged[:12]:
        dp = f"{x['k'][0][:28]} p{x['k'][1]}"
        print(f"{x['v']:<13}{dp:<42}{x['cat']:<14}{x['brec']*100:>5.0f}{x['js']:>6}{x['gap']:>+6.0f}")

    json.dump([{**x, "k": list(x["k"])} for x in rows],
              open("results/_poc_binding.json", "w"), indent=2)
    print("\n[-> results/_poc_binding.json]")


if __name__ == "__main__":
    main()
