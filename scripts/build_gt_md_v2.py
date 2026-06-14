#!/usr/bin/env python3
"""Build GROUND_TRUTH.md v2 — a CORRECTED transcription of the figure-dense pages.

The v1 GT (build_gt_md.py) used a single gpt-5 vision pass on a 1600px render. An independent
audit + a text-layer diff (scripts/gt_textlayer_audit.py) showed it drops/misreads ~14% of
PRINTED numbers on Chart/Diagram pages (hallucinating plausible-but-wrong series, mis-mapping
series to colors, omitting churn bars), because at 1600px small labels are illegible.

v2 fixes the two root causes WITHOUT changing the builder model (gpt-5 stays the builder so it
keeps its ◆ upper-bound flag and Gemini stays cleanly graded):
  1. The exact PDF TEXT LAYER is supplied and declared AUTHORITATIVE for every printed value.
  2. The page is re-rendered at higher DPI (~2400px) so series/segment assignment is legible.

Only worklist pages (all Chart/Diagram + Mixed, plus any Table/Cover page the text-layer diff
flagged with >=6 missing printed numbers) are rebuilt; all other pages are copied verbatim from
v1 (they audited faithful at 97-99% printed-number recall). Per-page cache, resumable.

Output: ground_truth/GROUND_TRUTH_v2.md  +  results/_gt_markdown_v2.json
Usage:  python3 scripts/build_gt_md_v2.py [workers]
"""
import os, sys, json, time, base64, glob, threading
from concurrent.futures import ThreadPoolExecutor
import fitz
from openai import OpenAI

if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = _l.split("=", 1)[1].strip()

MODEL = "gpt-5"
PRICE_IN, PRICE_OUT = 1.25, 10.0
CACHE = "ground_truth/gt_markdown_v2/raw"
RENDER_MAXDIM = 2400
TL_CAP = 9000

PROMPT = (
"You are a meticulous document transcriber producing a CORRECTED GROUND-TRUTH reference for ONE page "
"of a born-digital business PDF. You are given (1) a high-resolution image of the page and (2) the "
"page's EXACT TEXT LAYER extracted directly from the PDF.\n\n"
"CRITICAL RULES:\n"
"- The TEXT LAYER is AUTHORITATIVE for every PRINTED character and number. Transcribe printed text and "
"numbers EXACTLY as they appear in the text layer — never 'smooth', round, or guess a printed value, and "
"never replace a printed number with an estimate. If the text layer prints 185, 184, 201 as data labels, "
"those are the values — do not emit 165, 166, 135.\n"
"- Use the IMAGE only to (a) assign each printed value to the CORRECT series / stacked segment / table "
"row / column / node — read the colors and positions carefully so series identities are not swapped; "
"(b) read the geometry of LABEL-FREE points (bars/lines with NO printed label) — prefix those with ~; "
"(c) capture structure, relationships, and any negative/below-axis bars (e.g. churn) that are easy to miss.\n"
"- Render EVERY table as a GitHub-markdown table with all rows/cells/headers, numbers exact. Reproduce "
"sparse mark columns (checkmarks/icons) on the CORRECT rows.\n"
"- For EVERY chart write a line starting `**Chart:**` giving type, title, axis labels with scale/ticks, each "
"series name, and the per-point DATA VALUES (printed values exact; ~ only for unlabeled points), plus any "
"below-axis / negative series. For diagrams write `**Diagram:**` (nodes, labels, relationships). For "
"photos/logos write `**Image:**` / `**Logo:**`.\n\n"
"Output ONLY the corrected Markdown transcription of the page — no preamble, no commentary."
)

_local = threading.local()
def client():
    if not hasattr(_local, "c"): _local.c = OpenAI()
    return _local.c

_docs = {}
_lock = threading.Lock()
def render_and_text(pdf_path, page0):
    with _lock:
        if pdf_path not in _docs:
            _docs[pdf_path] = fitz.open(pdf_path)
        pg = _docs[pdf_path][page0]
        zoom = 2.0
        longside = max(pg.rect.width, pg.rect.height) * zoom
        if longside > RENDER_MAXDIM:
            zoom *= RENDER_MAXDIM / longside
        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        png = pix.tobytes("png")
        text = pg.get_text()
    return base64.b64encode(png).decode(), text


def transcribe(pdf_path, page0):
    b64, textlayer = render_and_text(pdf_path, page0)
    user_text = (PROMPT + "\n\n===== EXACT TEXT LAYER (authoritative for printed values) =====\n"
                 + (textlayer or "(no text layer)")[:TL_CAP])
    content = [{"type": "input_text", "text": user_text},
               {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"}]
    last = None
    for attempt in range(4):
        try:
            t0 = time.perf_counter()
            r = client().responses.create(model=MODEL, reasoning={"effort": "medium"},
                                          input=[{"role": "user", "content": content}],
                                          max_output_tokens=16000)
            it, ot = r.usage.input_tokens, r.usage.output_tokens
            return {"md": r.output_text or "", "in_tok": it, "out_tok": ot,
                    "cost_usd": round((it * PRICE_IN + ot * PRICE_OUT) / 1e6, 6),
                    "seconds": round(time.perf_counter() - t0, 2),
                    "status": getattr(r, "status", None)}
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    return {"md": "", "error": str(last), "in_tok": 0, "out_tok": 0, "cost_usd": 0.0, "seconds": 0.0}


def build_worklist():
    key = json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))
    labels = {(p["doc"], p["page"]): p["final_label"] for p in key["pages"]}
    diff = {(r["doc"], r["page"]): r for r in json.load(open("results/gt_audit_v2/textlayer_diff.json"))}
    work = set()
    for (doc, page), lab in labels.items():
        d = diff.get((doc, page), {})
        if lab in ("Chart/Diagram", "Mixed") or d.get("missing_printed", 0) >= 6:
            work.add((doc, page))
    return work, labels


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    os.makedirs(CACHE, exist_ok=True)
    work, labels = build_worklist()
    v1 = {(r["doc"], r["page"]): r for r in json.load(open("results/_gt_markdown.json"))}
    pdfs = {os.path.splitext(os.path.basename(p))[0]: p for p in glob.glob("Data/*.pdf")}
    print(f"worklist: {len(work)} pages to rebuild; {len(v1)-len(work)} copied from v1")

    def task(dp):
        doc, page = dp
        cp = os.path.join(CACHE, f"{doc}__p{page:04d}.json")
        if os.path.exists(cp):
            return json.load(open(cp))
        res = transcribe(pdfs[doc], page - 1)
        res["doc"], res["page"] = doc, page
        json.dump(res, open(cp, "w"))
        return res

    targets = sorted(work)
    t0 = time.time(); rebuilt = {}; done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(task, dp): dp for dp in targets}
        for f in list(futs):
            r = f.result(); rebuilt[(r["doc"], r["page"])] = r; done += 1
            if done % 20 == 0:
                c = sum(x.get("cost_usd", 0) for x in rebuilt.values())
                print(f"  {done}/{len(targets)} ({time.time()-t0:.0f}s, ${c:.2f})", flush=True)

    # merge: rebuilt where in worklist, else v1
    merged = []
    for dp, r1 in v1.items():
        if dp in rebuilt and rebuilt[dp].get("md"):
            rr = dict(rebuilt[dp]); rr["rebuilt"] = True
            merged.append(rr)
        else:
            r = dict(r1); r["rebuilt"] = False; merged.append(r)
    merged.sort(key=lambda r: (r["doc"], r["page"]))

    L = ["# GROUND TRUTH v2 — corrected transcription (gpt-5 vision + authoritative text layer)\n"]
    for r in merged:
        L.append(f"\n\n---\n\n## {r['doc']} — page {r['page']}\n")
        L.append((r.get("md") or "").strip() or "*(empty)*")
    open("ground_truth/GROUND_TRUTH_v2.md", "w").write("\n".join(L) + "\n")
    json.dump(merged, open("results/_gt_markdown_v2.json", "w"))
    cost = sum(x.get("cost_usd", 0) for x in rebuilt.values())
    errs = [x for x in rebuilt.values() if x.get("error")]
    print(f"\nv2 built: rebuilt {len(rebuilt)} pages; cost ${cost:.2f}; errors {len(errs)}")
    print("-> ground_truth/GROUND_TRUTH_v2.md  +  results/_gt_markdown_v2.json")


if __name__ == "__main__":
    main()
