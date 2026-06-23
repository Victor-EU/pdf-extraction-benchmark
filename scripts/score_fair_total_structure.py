#!/usr/bin/env python3
"""STRUCTURE-AWARE fair total — the canonical headline metric (2026-06-14).

Supersedes the pure information-PRESENCE rubric (score_fair_total.py, preserved; its output is
kept as results/_fair_total_judging_content.json, the "content presence" diagnostic). Rationale:
on finance / M&A / consulting documents a value bound to the WRONG row, column, entity, or node
is an ACTIVE downstream error — worse than an omission, which is at least visibly missing. The
content rubric credited token PRESENCE and so over-credited tools that recover characters but
destroy structure (see AUDIT_PYMUPDF_STRUCTURE.md). This metric prices structure into recall and
fidelity directly, with NO arbitrary dimension weighting:

  - info_recall now means "fraction of GT facts conveyed WITH THEIR BINDINGS RECOVERABLE" — which
    row/column/series/node/entity each value belongs to. Tokens present but with bindings
    destroyed (scrambled, flattened, merged) do NOT count. Correct structure stated in prose gets
    full credit (this is NOT a formatting/verbosity test). On a page with no tabular/diagrammatic
    structure (plain prose, a cover) it reduces to ordinary content recall, so unstructured pages
    are not penalized.
  - unsupported now explicitly counts an ACTIVELY WRONG BINDING (a value asserted under the wrong
    key) as a contradiction — penalizing misbinding harder than omission. A flat dump that does
    not assert a binding is only low-recall, not unsupported.

Both judge families (gpt-5 here, Gemini via score_fair_total_structure_gemini.py which imports
this PROMPT_HEAD) use the byte-identical rubric. Output: results/_fair_total_judging.json
(the NEW canonical). Set SS_ONLY=diagram to restrict to the relational-diagram subset.
"""
import os, sys, json, time, random, threading
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_vendor_md import VENDORS, load_pages

if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = _l.split("=", 1)[1].strip()

MODEL = "gpt-5"
PRICE_IN, PRICE_OUT = 1.25, 10.0
LETTERS = "ABCDEFGHIJKL"
GT_CAP = int(os.environ.get("FT_GT_CAP", "16000"))
VEND_CAP = int(os.environ.get("FT_VEND_CAP", "16000"))

PROMPT_HEAD = (
"You are a STRICT, BLIND grader of document-extraction quality for DOWNSTREAM USE. The documents "
"are ADMINISTRATIVE / INSURANCE forms (employer attestations, benefit-claim and social-aid forms): "
"forms, tables, and prose. Below is a GROUND-TRUTH transcription of ONE page, then several parser "
"extractions of the same page, labeled A, B, C, ...\n\n"
"The GROUND TRUTH lists the page's real information AND its structure: prose, table rows/columns, "
"FORM FIELDS (each printed label and its filled-in value), and CHECKBOX / RADIO options WITH their "
"checked-or-unchecked state — i.e. which value belongs to which field label, which cell to which "
"row/column, and which option is ticked.\n\n"
"GUIDING PRINCIPLE: a value attached to the WRONG label (wrong field, wrong row/column) OR a "
"checkbox reported with the WRONG state (ticked when it is blank, or blank when it is ticked) is an "
"ACTIVE ERROR that corrupts anything built on top of it — strictly worse than a value that is "
"simply missing. Grade so that preserving correct bindings AND correct checkbox states is what "
"matters, not merely listing the right characters.\n\n"
"TASK:\n"
"1) page_info_weight (1-10): how much substantive STRUCTURED information does this page hold per "
"the ground truth? 1 = nearly empty (a title/address block only); 5 = a normal prose or part-form "
"page; 10 = very dense (a large multi-field form, a big multi-column table, or many checkboxes with "
"many bindings).\n"
"2) For EACH extraction, grade ONLY against the ground truth, and CREDIT EQUIVALENT PHRASING: a "
"form/table described in DIFFERENT WORDS that conveys the same facts AND THE SAME STRUCTURE (same "
"value-to-field, value-to-row, value-to-column bindings, and the same checkbox states) is fully "
"captured. Correct structure stated in prose earns FULL credit — this is NOT a formatting, layout "
"or verbosity test.\n"
"   - info_recall (0-100): what fraction of the ground truth's substantive information does this "
"extraction convey SUCH THAT A READER COULD RECOVER THE CORRECT BINDINGS — which value goes with "
"which field label, which value with which row/column, and the correct checked/unchecked state of "
"each option? CRITICAL: tokens present but with their bindings DESTROYED do NOT count. If an "
"extraction lists field values but not which label each belongs to, or dumps a checkbox list "
"without saying which boxes are ticked, or scrambles/flattens a table so the reader CANNOT tell "
"which value belongs to which row, score it LOW (typically 20-50) EVEN THOUGH the raw tokens are "
"all present. On a page that is plain prose (a cover letter, instructions) with no fields/table, "
"just grade ordinary completeness of the facts. Reward RECOVERABLE STRUCTURE, not token presence. "
"On form/table-dense pages, missing the actual filled-in values or checkbox states must also lower "
"this heavily.\n"
"   - unsupported (0-100): what fraction of THIS extraction's substantive claims CONTRADICT the "
"ground truth or assert specific facts/values that are clearly WRONG or invented? This INCLUDES an "
"actively WRONG BINDING — a value placed under the wrong field/row/column — and a WRONG CHECKBOX "
"STATE (reporting an option ticked when the ground truth shows it blank, or vice-versa) — because "
"downstream that is a wrong fact. (A flat dump that does not assert a binding at all is only "
"low-recall, not unsupported.) Do NOT penalize a longer but consistent description. 0 if nothing "
"it says conflicts with the page.\n"
"Grade strictly and differentiate the parsers. An extraction that is empty or near-empty gets "
"info_recall near 0."
)


def schema(letters):
    props = {L: {"type": "object", "additionalProperties": False,
                 "properties": {"info_recall": {"type": "integer"},
                                "unsupported": {"type": "integer"}},
                 "required": ["info_recall", "unsupported"]} for L in letters}
    return {"type": "object", "additionalProperties": False,
            "properties": {"page_info_weight": {"type": "integer"},
                           "scores": {"type": "object", "additionalProperties": False,
                                      "properties": props, "required": list(letters)}},
            "required": ["page_info_weight", "scores"]}


_local = threading.local()
def client():
    if not hasattr(_local, "c"):
        _local.c = OpenAI()
    return _local.c


def judge_page(doc, page, gt_md, vendor_md):
    rnd = random.Random(f"{doc}:{page}")          # SAME seed as canonical content run
    order = VENDORS[:]; rnd.shuffle(order)
    letters = LETTERS[:len(order)]
    mapping = dict(zip(letters, order))
    blocks = [PROMPT_HEAD, f"\n===== GROUND TRUTH (page reference) =====\n{(gt_md or '')[:GT_CAP]}"]
    for L in letters:
        blob = (vendor_md[mapping[L]].get((doc, page), "") or "(no extraction)")[:VEND_CAP]
        blocks.append(f"\n===== EXTRACTION {L} =====\n{blob}")
    text = "\n".join(blocks)
    fmt = {"format": {"type": "json_schema", "name": "fair_total_structure", "strict": True,
                      "schema": schema(letters)}}
    last = None
    for attempt in range(4):
        try:
            r = client().responses.create(model=MODEL, reasoning={"effort": "low"},
                                          input=[{"role": "user", "content":
                                                  [{"type": "input_text", "text": text}]}],
                                          text=fmt, max_output_tokens=4000)
            obj = json.loads(r.output_text)
            it, ot = r.usage.input_tokens, r.usage.output_tokens
            cost = (it * PRICE_IN + ot * PRICE_OUT) / 1e6
            scores = {mapping[L]: obj["scores"][L] for L in letters}
            return {"doc": doc, "page": page, "weight": obj["page_info_weight"],
                    "scores": scores, "cost_usd": round(cost, 6)}
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    return {"doc": doc, "page": page, "error": str(last), "scores": {}}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    cache_dir = os.environ.get("FT_CACHE", "ground_truth/fair_total_structure_judge")
    out_path = os.environ.get("FT_OUT", "results/_fair_total_judging.json")
    gt_path = os.environ.get("GT_MD", "results/_gt_markdown.json")
    gt = {(r["doc"], r["page"]): r.get("md", "") for r in json.load(open(gt_path))}
    targets = sorted(gt.keys())
    if os.environ.get("SS_ONLY") == "diagram":
        fj = json.load(open("results/_figure_judging.json"))
        keep = {(r["doc"], r["page"]) for r in fj if r.get("diagrams")}
        targets = [t for t in targets if t in keep]
    vendor_md = {vd: load_pages(vd) for vd in VENDORS}
    os.makedirs(cache_dir, exist_ok=True)
    print(f"STRUCTURE-AWARE fair total: {len(targets)} pages, {len(VENDORS)} vendors -> {out_path}")

    def task(dp):
        cp = os.path.join(cache_dir, f"{dp[0]}__p{dp[1]:04d}.json")
        if os.path.exists(cp):
            return json.load(open(cp))
        res = judge_page(dp[0], dp[1], gt.get(dp, ""), vendor_md)
        json.dump(res, open(cp, "w"))
        return res

    t0 = time.time(); out = []; done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(task, dp) for dp in targets]
        for f in futs:
            out.append(f.result()); done += 1
            if done % 25 == 0:
                c = sum(r.get("cost_usd", 0) for r in out)
                print(f"  {done}/{len(targets)} ({time.time()-t0:.0f}s, ${c:.2f})", flush=True)
    json.dump(out, open(out_path, "w"), indent=2)
    errs = [r for r in out if r.get("error")]
    print(f"judged {len(out)} pages; errors {len(errs)}; "
          f"cost ${sum(r.get('cost_usd',0) for r in out):.2f}")


if __name__ == "__main__":
    main()
