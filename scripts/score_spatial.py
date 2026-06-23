#!/usr/bin/env python3
"""SPATIAL-RELATIONSHIP fidelity judge for insurance forms.

On a form, a value's meaning lives entirely in its 2-D position relative to a label, a checkbox,
or a table cell. A perfect OCR that flattens the page is useless. This judge therefore scores ONLY
the spatial relationships — not prose recall — decomposed into the three that matter on these forms:

  - field_value_binding : of the GT's printed-label -> filled-value pairs, what fraction does the
    extraction reproduce with the value ATTACHED TO THE RIGHT LABEL? (the value appearing somewhere
    on the page, detached from its label, does NOT count.)
  - checkbox_state      : of the GT's checkbox/radio options, what fraction does the extraction
    report with the CORRECT ticked/blank state, BOUND TO THE RIGHT OPTION? (a checkbox read ticked
    when blank, or blank when ticked, is an active error.)
  - table_cell_binding  : of the GT's table cells, what fraction sit in the CORRECT row x column?

Each has a `_present` flag (the GT page contains that relationship type). The per-page composite
weights the pure form-spatial calls (field, checkbox) above table cells. Blind + shuffled; both
judge families (JUDGE=gpt5 default, or JUDGE=gemini). Respects the LA_DPT2 hook.

Usage:  JUDGE=gpt5 python3 scripts/score_spatial.py [workers]
Output: results/_spatial_judging[_gemini].json
"""
import os, sys, json, time, random, threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_vendor_md import VENDORS, load_pages

for _l in (open(".env") if os.path.exists(".env") else []):
    for k in ("OPENAI_API_KEY", "GEMINI_API_KEY"):
        if _l.startswith(k + "="):
            os.environ[k] = _l.split("=", 1)[1].strip()

JUDGE = os.environ.get("JUDGE", "gpt5")
LETTERS = "ABCDEFGHIJKL"
GT_CAP = VEND_CAP = 16000
# composite weights: forms are field/checkbox-centric; table cells slightly less central
W = {"field_value_binding": 1.0, "checkbox_state": 1.0, "table_cell_binding": 0.8}

PROMPT_HEAD = (
"You are a STRICT, BLIND grader of how well a parser preserved the SPATIAL RELATIONSHIPS of an "
"ADMINISTRATIVE / INSURANCE FORM. The documents are employer attestations and benefit/social-aid "
"forms. Below is a GROUND-TRUTH transcription of ONE page (it lists every printed field LABEL and "
"its filled-in VALUE, every CHECKBOX/RADIO option with its ticked-or-blank state, and any TABLE "
"with its rows and columns), then several parser extractions of the same page, labeled A, B, C ...\n\n"
"On a form, a value's meaning comes ENTIRELY from its position: which label it sits next to, which "
"option a tick belongs to, which row x column a cell occupies. A parser that recovers all the right "
"characters but DETACHES them from their position has captured nothing usable. Grade ONLY the "
"spatial relationships below — ignore prose fluency, formatting, and verbosity. Credit equivalent "
"phrasing (a field stated as 'SIRET: 333...' or 'SIRET = 333...' both bind correctly).\n\n"
"For EACH extraction, output three sub-scores. For each, first decide from the GROUND TRUTH whether "
"the page CONTAINS that relationship type at all; if it does not, set its *_present flag false (its "
"score is ignored).\n"
"  - field_value_binding (0-100): of the GT's label->value pairs, the fraction this extraction "
"conveys with the value UNAMBIGUOUSLY ATTACHED TO THE CORRECT LABEL. A value present but stranded "
"from its label (e.g. a flat run of all labels then, separately, a run of all values) scores LOW "
"even though the characters are all there. A value bound to the WRONG label is an active error.\n"
"  - checkbox_state (0-100): of the GT's checkbox/radio options, the fraction this extraction "
"reports with the CORRECT ticked/blank state bound to the RIGHT option. Reporting a box ticked when "
"the GT shows it blank (or vice-versa), or not representing checkbox state at all, scores LOW. This "
"is the most consequential, purely-spatial call on these forms.\n"
"  - table_cell_binding (0-100): of the GT's table cells, the fraction this extraction places in "
"the CORRECT row x column. Cells dumped as a flat list whose row/column membership cannot be "
"recovered score LOW.\n"
"Also output page_spatial_weight (1-10): how much SPATIAL form-structure this page holds per the GT "
"(1 = almost pure prose / a cover letter; 10 = a dense field+checkbox+table grid). Grade strictly "
"and differentiate the parsers."
)


def schema_gpt5(letters):
    sub = {"type": "object", "additionalProperties": False, "properties": {
        "field_value_binding": {"type": "integer"}, "field_present": {"type": "boolean"},
        "checkbox_state": {"type": "integer"}, "checkbox_present": {"type": "boolean"},
        "table_cell_binding": {"type": "integer"}, "table_present": {"type": "boolean"}},
        "required": ["field_value_binding", "field_present", "checkbox_state",
                     "checkbox_present", "table_cell_binding", "table_present"]}
    props = {L: sub for L in letters}
    return {"type": "object", "additionalProperties": False,
            "properties": {"page_spatial_weight": {"type": "integer"},
                           "scores": {"type": "object", "additionalProperties": False,
                                      "properties": props, "required": list(letters)}},
            "required": ["page_spatial_weight", "scores"]}


def schema_gemini(letters):
    sub = {"type": "object", "properties": {
        "field_value_binding": {"type": "integer"}, "field_present": {"type": "boolean"},
        "checkbox_state": {"type": "integer"}, "checkbox_present": {"type": "boolean"},
        "table_cell_binding": {"type": "integer"}, "table_present": {"type": "boolean"}},
        "required": ["field_value_binding", "field_present", "checkbox_state",
                     "checkbox_present", "table_cell_binding", "table_present"],
        "propertyOrdering": ["field_value_binding", "field_present", "checkbox_state",
                             "checkbox_present", "table_cell_binding", "table_present"]}
    return {"type": "object", "properties": {
        "page_spatial_weight": {"type": "integer"},
        "scores": {"type": "object", "properties": {L: sub for L in letters},
                   "required": list(letters), "propertyOrdering": list(letters)}},
        "required": ["page_spatial_weight", "scores"],
        "propertyOrdering": ["page_spatial_weight", "scores"]}


_local = threading.local()
def gpt5_client():
    if not hasattr(_local, "c"):
        from openai import OpenAI
        _local.c = OpenAI()
    return _local.c


def build_prompt(doc, page, gt_md, vendor_md):
    rnd = random.Random(f"spatial:{doc}:{page}")
    order = VENDORS[:]; rnd.shuffle(order)
    letters = LETTERS[:len(order)]
    mapping = dict(zip(letters, order))
    blocks = [PROMPT_HEAD, f"\n===== GROUND TRUTH (page reference) =====\n{(gt_md or '')[:GT_CAP]}"]
    for L in letters:
        blob = (vendor_md[mapping[L]].get((doc, page), "") or "(no extraction)")[:VEND_CAP]
        blocks.append(f"\n===== EXTRACTION {L} =====\n{blob}")
    return "\n".join(blocks), mapping, letters


def judge_page(doc, page, gt_md, vendor_md):
    text, mapping, letters = build_prompt(doc, page, gt_md, vendor_md)
    last = None
    for attempt in range(4):
        try:
            if JUDGE == "gpt5":
                fmt = {"format": {"type": "json_schema", "name": "spatial", "strict": True,
                                  "schema": schema_gpt5(letters)}}
                r = gpt5_client().responses.create(model="gpt-5", reasoning={"effort": "low"},
                        input=[{"role": "user", "content": [{"type": "input_text", "text": text}]}],
                        text=fmt, max_output_tokens=4000)
                obj = json.loads(r.output_text)
                cost = (r.usage.input_tokens * 1.25 + r.usage.output_tokens * 10.0) / 1e6
            else:
                import requests, certifi
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
                body = {"contents": [{"role": "user", "parts": [{"text": text}]}],
                        "generationConfig": {"responseMimeType": "application/json",
                                             "responseSchema": schema_gemini(letters),
                                             "thinkingConfig": {"thinkingLevel": "minimal"},
                                             "temperature": 0, "maxOutputTokens": 8000}}
                resp = requests.post(url, headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"],
                                     "Content-Type": "application/json"}, json=body,
                                     verify=certifi.where(), timeout=180)
                if resp.status_code == 429 or resp.status_code >= 500:
                    last = f"HTTP {resp.status_code}"; time.sleep(5 * (attempt + 1)); continue
                resp.raise_for_status()
                j = resp.json(); cand = (j.get("candidates") or [{}])[0]
                txt = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts", [])
                              if not p.get("thought"))
                obj = json.loads(txt)
                u = j.get("usageMetadata", {})
                cost = (u.get("promptTokenCount", 0) * 1.5 +
                        (u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)) * 9.0) / 1e6
            scores = {mapping[L]: obj["scores"][L] for L in letters}
            return {"doc": doc, "page": page, "weight": obj["page_spatial_weight"],
                    "scores": scores, "cost_usd": round(cost, 6)}
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    return {"doc": doc, "page": page, "error": str(last), "scores": {}}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    out_path = os.environ.get("SP_OUT",
               "results/_spatial_judging%s.json" % ("" if JUDGE == "gpt5" else "_gemini"))
    gt = {(r["doc"], r["page"]): r.get("md", "") for r in json.load(open("results/_gt_markdown.json"))}
    vendor_md = {vd: load_pages(vd) for vd in VENDORS}
    targets = sorted(gt.keys())
    print(f"SPATIAL judge ({JUDGE}): {len(targets)} pages, {len(VENDORS)} vendors -> {out_path}")
    out = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(judge_page, d, p, gt[(d, p)], vendor_md) for (d, p) in targets]
        for f in futs:
            out.append(f.result())
    json.dump(out, open(out_path, "w"), indent=2)
    errs = [r for r in out if r.get("error")]
    print(f"judged {len(out)} pages; errors {len(errs)}; cost ${sum(r.get('cost_usd',0) for r in out):.2f}")


if __name__ == "__main__":
    main()
