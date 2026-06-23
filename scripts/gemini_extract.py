#!/usr/bin/env python3
"""Gemini FULL-EXTRACTION harness — the Gemini twin of openai_extract.py.

Runs gemini-3.5-flash and gemini-3.1-flash-lite over every page asking for the SAME
block reconstruction (text / table / typed figure with recovered graph data) using the
IDENTICAL prompt imported from openai_extract.py, so the comparison isolates the MODEL.

REST via requests+certifi (matches llamaparse_fetch / landingai_pass; sidesteps the macOS
python.org SSL CERTIFICATE_VERIFY_FAILED gotcha). thinkingLevel=minimal is the Gemini-3.x
analog of gpt-5 reasoning effort=low. Resumable per-page cache, threaded.

Usage:  python3 scripts/gemini_extract.py <gemini-3.5-flash|gemini-3.1-flash-lite> [image|file] [workers]
Output: results/_gemini_<slug>_extract.json  +  ground_truth/gemini_<slug>_extract/raw/
"""
import os, sys, json, time, base64, threading
from concurrent.futures import ThreadPoolExecutor
import fitz, requests, certifi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openai_extract import PROMPT  # identical instruction text across vendors
from corpus import discover_pdfs

if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("GEMINI_API_KEY="):
            os.environ["GEMINI_API_KEY"] = _l.split("=", 1)[1].strip()
API_KEY = os.environ["GEMINI_API_KEY"]

# (input $/M, output $/M) — output billed = candidates + thinking tokens
PRICES = {"gemini-3.5-flash": (1.50, 9.00), "gemini-3.1-flash-lite": (0.25, 1.50)}
SLUG   = {"gemini-3.5-flash": "gemini_flash", "gemini-3.1-flash-lite": "gemini_flash_lite"}

# Gemini responseSchema: lowercase types, enum arrays, no additionalProperties, propertyOrdering.
# Enums kept byte-identical to openai_extract.SCHEMA so both models answer in the same shape.
_ITEM = {
    "type": "object",
    "properties": {
        "type": {"type": "string",
                 "enum": ["text", "heading", "field", "choice", "table",
                          "figure", "marginalia", "other"]},
        "position": {"type": "string",
                     "enum": ["top-left", "top-center", "top-right", "mid-left", "center",
                              "mid-right", "bottom-left", "bottom-center", "bottom-right",
                              "full-page"]},
        "field_label": {"type": "string"},
        "field_value": {"type": "string"},
        "choice_label": {"type": "string"},
        "choice_state": {"type": "string", "enum": ["checked", "unchecked", "none"]},
        "figure_kind": {"type": "string", "enum": ["none", "photo", "logo"]},
        "content": {"type": "string"},
    },
    "required": ["type", "position", "field_label", "field_value",
                 "choice_label", "choice_state", "figure_kind", "content"],
    "propertyOrdering": ["type", "position", "field_label", "field_value",
                         "choice_label", "choice_state", "figure_kind", "content"],
}
SCHEMA = {
    "type": "object",
    "properties": {"blocks": {"type": "array", "items": _ITEM}},
    "required": ["blocks"],
    "propertyOrdering": ["blocks"],
}

_docs = {}
_docs_lock = threading.Lock()
def page_pdf_b64(pdf_path, page0):
    with _docs_lock:
        if pdf_path not in _docs:
            _docs[pdf_path] = fitz.open(pdf_path)
        one = fitz.open()
        one.insert_pdf(_docs[pdf_path], from_page=page0, to_page=page0)
        b = one.tobytes(); one.close()
    return base64.b64encode(b).decode()


def call(model, mode, png_path, pdf_path, page0):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"x-goog-api-key": API_KEY, "Content-Type": "application/json"}
    if mode == "image":
        b64 = base64.b64encode(open(png_path, "rb").read()).decode()
        media = {"inline_data": {"mime_type": "image/png", "data": b64}}
    else:
        media = {"inline_data": {"mime_type": "application/pdf",
                                 "data": page_pdf_b64(pdf_path, page0)}}
    body = {
        "contents": [{"role": "user", "parts": [{"text": PROMPT}, media]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA,
            "thinkingConfig": {"thinkingLevel": "minimal"},
            "temperature": 0,
            "maxOutputTokens": 16000,
        },
    }
    pin, pout = PRICES[model]
    t0 = time.perf_counter(); last = None
    for attempt in range(6):
        try:
            r = requests.post(url, headers=headers, json=body,
                              verify=certifi.where(), timeout=180)
            if r.status_code == 429 or r.status_code >= 500:
                last = f"HTTP {r.status_code}: {r.text[:200]}"
                time.sleep(min(60, 5 * (attempt + 1) ** 2)); continue
            r.raise_for_status()
            j = r.json()
            dt = time.perf_counter() - t0
            cand = (j.get("candidates") or [{}])[0]
            finish = cand.get("finishReason")
            parts = (cand.get("content") or {}).get("parts", []) or []
            txt = "".join(p.get("text", "") for p in parts if not p.get("thought"))
            u = j.get("usageMetadata", {})
            it = u.get("promptTokenCount", 0)
            ot = u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)
            cost = (it * pin + ot * pout) / 1e6
            try:
                blocks = json.loads(txt).get("blocks", [])
            except Exception:
                blocks = []
                last = f"parse-fail finish={finish} len={len(txt)}"
                if finish == "MAX_TOKENS":
                    # genuinely truncated; record and stop retrying
                    return {"blocks": [], "error": last, "seconds": round(dt, 2),
                            "in_tok": it, "out_tok": ot, "cost_usd": round(cost, 6),
                            "status": "incomplete"}
            return {"blocks": blocks, "seconds": round(dt, 2),
                    "in_tok": it, "out_tok": ot, "cost_usd": round(cost, 6),
                    "status": finish}
        except Exception as e:
            last = str(e); time.sleep(3 * (attempt + 1))
    return {"blocks": [], "error": str(last), "seconds": 0.0,
            "in_tok": 0, "out_tok": 0, "cost_usd": 0.0}


def main():
    model = sys.argv[1]
    assert model in PRICES, f"model must be one of {list(PRICES)}"
    mode = sys.argv[2] if len(sys.argv) > 2 else "image"
    assert mode in ("image", "file")
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    render = "ground_truth/render_full"
    slug = SLUG[model] + ("" if mode == "image" else f"_{mode}")
    cache_dir = f"ground_truth/gemini_{slug}_extract/raw"
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs("results", exist_ok=True)

    manifest = json.load(open(os.path.join(render, "_manifest.json")))
    pdfs = discover_pdfs()

    def task(m):
        doc, page = m["doc"], m["page"]
        cpath = os.path.join(cache_dir, f"{doc}__p{page:04d}.json")
        if os.path.exists(cpath):
            return json.load(open(cpath))
        res = call(model, mode, os.path.join(render, m["png"]), pdfs[doc], page - 1)
        res["doc"], res["page"] = doc, page
        json.dump(res, open(cpath, "w"), indent=2)
        return res

    t0 = time.time(); results = [None] * len(manifest); done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(task, m): i for i, m in enumerate(manifest)}
        for fut in list(futs):
            results[futs[fut]] = fut.result()
            done += 1
            if done % 25 == 0:
                cost = sum(r.get("cost_usd", 0) for r in results if r)
                print(f"  {done}/{len(manifest)} ({time.time()-t0:.0f}s, ${cost:.2f})", flush=True)

    results.sort(key=lambda r: (r["doc"], r["page"]))
    json.dump(results, open(f"results/_gemini_{slug}_extract.json", "w"), indent=2)
    errs = [r for r in results if r.get("error")]
    tot = sum(r.get("cost_usd", 0) for r in results)
    secs = [r["seconds"] for r in results if r.get("seconds")]
    trunc = [r for r in results if r.get("status") == "incomplete"]
    print(f"\nEXTRACT {model} mode={mode}: {len(results)} pages in {time.time()-t0:.0f}s "
          f"({workers} workers); mean {sum(secs)/len(secs):.2f}s/pg; cost ${tot:.2f}; "
          f"errors {len(errs)}; truncated {len(trunc)}")


if __name__ == "__main__":
    main()
