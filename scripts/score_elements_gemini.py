#!/usr/bin/env python3
"""Cross-family element judge — Gemini instead of gpt-5, on the SAME fixed GT element inventory.

Confirms the per-element-type 'who is good at what' winners are not an artifact of the gpt-5 judge.
Byte-identical prompt (PROMPT_HEAD from score_elements), same blind per-page shuffle seed, same caps,
same Stage-A element list — only the judge model family changes.
Output: results/_element_judging_gemini.json
"""
import os, sys, json, time, random
from concurrent.futures import ThreadPoolExecutor
import requests, certifi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score_elements import PROMPT_HEAD, VEND_CAP, LETTERS
from build_vendor_md import VENDORS, load_pages

if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("GEMINI_API_KEY="):
            os.environ["GEMINI_API_KEY"] = _l.split("=", 1)[1].strip()
API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = os.environ.get("JUDGE_MODEL", "gemini-3.5-flash")
PRICE_IN, PRICE_OUT = 1.50, 9.00


def schema(ids, letters):
    sc = {"type": "object",
          "properties": {"recall": {"type": "integer"}, "wrong": {"type": "integer"}},
          "required": ["recall", "wrong"], "propertyOrdering": ["recall", "wrong"]}
    vendors = {"type": "object", "properties": {L: sc for L in letters},
               "required": list(letters), "propertyOrdering": list(letters)}
    item = {"type": "object",
            "properties": {"id": {"type": "string", "enum": ids}, "vendors": vendors},
            "required": ["id", "vendors"], "propertyOrdering": ["id", "vendors"]}
    return {"type": "object", "properties": {"elements": {"type": "array", "items": item}},
            "required": ["elements"], "propertyOrdering": ["elements"]}


def judge_page(doc, page, elements, vendor_md):
    if not elements:
        return {"doc": doc, "page": page, "scores": [], "cost_usd": 0.0}
    rnd = random.Random(f"{doc}:{page}")
    order = VENDORS[:]; rnd.shuffle(order)
    letters = LETTERS[:len(order)]
    mapping = dict(zip(letters, order))
    el_lines = [f"[{e['id']}] type={e['type']} | {e['label']} | key_facts: {e['key_facts']}"
                for e in elements]
    blocks = [PROMPT_HEAD, "\n===== GROUND-TRUTH ELEMENTS OF THIS PAGE =====\n" + "\n".join(el_lines)]
    for L in letters:
        blob = (vendor_md[mapping[L]].get((doc, page), "") or "(no extraction)")[:VEND_CAP]
        blocks.append(f"\n===== EXTRACTION {L} =====\n{blob}")
    text = "\n".join(blocks)
    ids = [e["id"] for e in elements]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {"x-goog-api-key": API_KEY, "Content-Type": "application/json"}
    body = {"contents": [{"role": "user", "parts": [{"text": text}]}],
            "generationConfig": {"responseMimeType": "application/json",
                                 "responseSchema": schema(ids, letters),
                                 "thinkingConfig": {"thinkingLevel": "minimal"},
                                 "temperature": 0, "maxOutputTokens": 12000}}
    last = None
    for attempt in range(6):
        try:
            r = requests.post(url, headers=headers, json=body, verify=certifi.where(), timeout=180)
            if r.status_code == 429 or r.status_code >= 500:
                last = f"HTTP {r.status_code}"; time.sleep(min(60, 5*(attempt+1)**2)); continue
            r.raise_for_status()
            j = r.json()
            cand = (j.get("candidates") or [{}])[0]
            parts = (cand.get("content") or {}).get("parts", []) or []
            txt = "".join(p.get("text", "") for p in parts if not p.get("thought"))
            u = j.get("usageMetadata", {})
            it = u.get("promptTokenCount", 0); ot = u.get("candidatesTokenCount", 0)+u.get("thoughtsTokenCount", 0)
            cost = (it*PRICE_IN + ot*PRICE_OUT)/1e6
            obj = json.loads(txt)
            scores = []
            for ent in obj["elements"]:
                vd = {mapping[L]: ent["vendors"][L] for L in letters if L in ent["vendors"]}
                scores.append({"id": ent["id"], "vendors": vd})
            return {"doc": doc, "page": page, "scores": scores, "cost_usd": round(cost, 6)}
        except Exception as e:
            last = e; time.sleep(3*(attempt+1))
    return {"doc": doc, "page": page, "scores": [], "error": str(last)}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    cache_dir = os.environ.get("EL_CACHE", "ground_truth/element_judge_gemini")
    out_path = os.environ.get("EL_OUT", "results/_element_judging_gemini.json")
    elems = {(r["doc"], r["page"]): r.get("elements", [])
             for r in json.load(open("results/_gt_elements.json"))}
    vendor_md = {vd: load_pages(vd) for vd in VENDORS}
    targets = sorted(elems.keys())
    os.makedirs(cache_dir, exist_ok=True)

    def task(dp):
        cp = os.path.join(cache_dir, f"{dp[0]}__p{dp[1]:04d}.json")
        if os.path.exists(cp): return json.load(open(cp))
        res = judge_page(dp[0], dp[1], elems[dp], vendor_md)
        json.dump(res, open(cp, "w")); return res

    t0 = time.time(); out = []; done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(task, dp) for dp in targets]
        for f in futs:
            out.append(f.result()); done += 1
            if done % 50 == 0:
                c = sum(r.get("cost_usd", 0) for r in out)
                print(f"  {done}/{len(targets)} ({time.time()-t0:.0f}s, ${c:.2f})", flush=True)
    json.dump(out, open(out_path, "w"), indent=2)
    errs = [r for r in out if r.get("error")]
    print(f"GEMINI element judge ({MODEL}): judged {len(out)}; errors {len(errs)}; "
          f"cost ${sum(r.get('cost_usd',0) for r in out):.2f}")


if __name__ == "__main__":
    main()
