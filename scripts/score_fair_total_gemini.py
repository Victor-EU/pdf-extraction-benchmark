#!/usr/bin/env python3
"""Cross-family JUDGE replication of the fair total — Gemini judge instead of gpt-5.

Addresses the half of the monoculture critique the GT-correction does not: "the JUDGE is gpt-5."
Re-judges every page with gemini-3.5-flash using the BYTE-IDENTICAL prompt, blind shuffle (same
per-page seed), and text caps as score_fair_total.py — so the ONLY variable changed is the judge
model family. If the vendor ranking reproduces under a non-OpenAI judge, judge-family bias is ruled
out. (Caveat: Gemini is itself a contestant; read its own rows with that in mind — but the gpt-5
judge already scored Gemini's figures ABOVE its own, so cross-family judges are not self-serving.)

Env: GT_MD (which GT to grade against), FT_OUT, FT_CACHE.
Output: results/_fair_total_judging_gemini_v2.json (default)
"""
import os, sys, json, time, random, threading
from concurrent.futures import ThreadPoolExecutor
import requests, certifi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score_fair_total import PROMPT_HEAD, GT_CAP, VEND_CAP, LETTERS
from build_vendor_md import VENDORS, load_pages

if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("GEMINI_API_KEY="):
            os.environ["GEMINI_API_KEY"] = _l.split("=", 1)[1].strip()
API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = os.environ.get("JUDGE_MODEL", "gemini-3.5-flash")
PRICE_IN, PRICE_OUT = 1.50, 9.00


def schema(letters):
    score = {"type": "object",
             "properties": {"info_recall": {"type": "integer"}, "unsupported": {"type": "integer"}},
             "required": ["info_recall", "unsupported"],
             "propertyOrdering": ["info_recall", "unsupported"]}
    return {"type": "object",
            "properties": {"page_info_weight": {"type": "integer"},
                           "scores": {"type": "object",
                                      "properties": {L: score for L in letters},
                                      "required": list(letters),
                                      "propertyOrdering": list(letters)}},
            "required": ["page_info_weight", "scores"],
            "propertyOrdering": ["page_info_weight", "scores"]}


def judge_page(doc, page, gt_md, vendor_md):
    rnd = random.Random(f"{doc}:{page}")
    order = VENDORS[:]; rnd.shuffle(order)
    letters = LETTERS[:len(order)]
    mapping = dict(zip(letters, order))
    blocks = [PROMPT_HEAD, f"\n===== GROUND TRUTH (page reference) =====\n{(gt_md or '')[:GT_CAP]}"]
    for L in letters:
        blob = (vendor_md[mapping[L]].get((doc, page), "") or "(no extraction)")[:VEND_CAP]
        blocks.append(f"\n===== EXTRACTION {L} =====\n{blob}")
    text = "\n".join(blocks)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {"x-goog-api-key": API_KEY, "Content-Type": "application/json"}
    body = {"contents": [{"role": "user", "parts": [{"text": text}]}],
            "generationConfig": {"responseMimeType": "application/json",
                                 "responseSchema": schema(letters),
                                 "thinkingConfig": {"thinkingLevel": "minimal"},
                                 "temperature": 0, "maxOutputTokens": 8000}}
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
            it = u.get("promptTokenCount", 0); ot = u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)
            cost = (it*PRICE_IN + ot*PRICE_OUT)/1e6
            obj = json.loads(txt)
            scores = {mapping[L]: obj["scores"][L] for L in letters}
            return {"doc": doc, "page": page, "weight": obj["page_info_weight"],
                    "scores": scores, "cost_usd": round(cost, 6)}
        except Exception as e:
            last = e; time.sleep(3*(attempt+1))
    return {"doc": doc, "page": page, "error": str(last), "scores": {}}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    cache_dir = os.environ.get("FT_CACHE", "ground_truth/fair_total_judge_gemini_v2")
    out_path = os.environ.get("FT_OUT", "results/_fair_total_judging_gemini_v2.json")
    gt_path = os.environ.get("GT_MD", "results/_gt_markdown_v2.json")
    gt = {(r["doc"], r["page"]): r.get("md", "") for r in json.load(open(gt_path))}
    vendor_md = {vd: load_pages(vd) for vd in VENDORS}
    targets = sorted(gt.keys())
    os.makedirs(cache_dir, exist_ok=True)

    def task(dp):
        cp = os.path.join(cache_dir, f"{dp[0]}__p{dp[1]:04d}.json")
        if os.path.exists(cp): return json.load(open(cp))
        res = judge_page(dp[0], dp[1], gt[dp], vendor_md)
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
    print(f"GEMINI judge ({MODEL}): judged {len(out)}; errors {len(errs)}; "
          f"cost ${sum(r.get('cost_usd',0) for r in out):.2f}")


if __name__ == "__main__":
    main()
