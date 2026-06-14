#!/usr/bin/env python3
"""Judge the FIGURE dimension: graph-data fidelity + diagram-structure fidelity.

For each figure-bearing page (key = Chart/Diagram or Mixed), a BLIND gpt-5 vision judge sees
the page image + all 5 vendors' full extractions (shuffled A-E), identifies the graphs/diagrams
actually present, and scores each vendor 0-100 on:
  - graph fidelity : chart type, title, axes+scale, series, DATA VALUES, trend  (finance graphs)
  - diagram fidelity: components/nodes, labels, relationships/flow

Each vendor gets its FULL extraction (text+tables+figures) so a vendor that recovered a chart's
data AS A TABLE (e.g. LlamaParse) is fairly credited. Output: results/_figure_judging.json
"""
import os, sys, json, base64, time, glob, random, threading
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI

if os.path.exists(".env"):
    for _l in open(".env"):
        if _l.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = _l.split("=", 1)[1].strip()

MODEL = "gpt-5"
PRICE_IN, PRICE_OUT = 1.25, 10.0
RENDER = "ground_truth/render_full"
# Default = canonical 8-vendor cross-vendor judge. Override via env for sub-studies
# (e.g. the Gemini image-vs-file A/B) WITHOUT disturbing the canonical cache/output.
VENDORS = os.environ.get("FIG_VENDORS",
    "gpt5_image,gpt5_file,gemini_flash,gemini_flash_lite,"
    "landingai,llamaparse,pymupdf,tesseract").split(",")
LETTERS = "ABCDEFGHIJKL"
# Per-item / count / whole-blob caps on the figure-grading input (env-overridable; defaults =
# original published values). Raised to no-truncation levels for the cap audit re-judge.
FIG_CAP = int(os.environ.get("FIG_FIG_CAP", "1600"))
TAB_CAP = int(os.environ.get("FIG_TAB_CAP", "1200"))
NFIG = int(os.environ.get("FIG_NFIG", "8"))
NTAB = int(os.environ.get("FIG_NTAB", "6"))
BLOB_CAP = int(os.environ.get("FIG_BLOB", "7000"))

PROMPT_HEAD = (
"You are a STRICT, BLIND grader of document-parsing quality. The image is ONE PDF page. Below are "
"extractions produced by several parsers, labeled A, B, C, ... Each tried to extract the page's full "
"content.\n\n"
"TASK:\n"
"1) From the IMAGE, list the GRAPHS (data charts: line/bar/pie/scatter/area/waterfall) and the "
"DIAGRAMS (schematics: flow/process/cycle/org-chart/value-chain/network) actually present. If there "
"are none of a kind, use an empty list.\n"
"2) For EACH extraction, grade ONLY against what is truly on the page (the image is ground truth):\n"
"   - graph_score 0-100: did it recover the graph(s)' DATA — chart type, title, axis labels & scale, "
"series names, the actual DATA VALUES (numbers), and trend? Reward recovered numbers heavily; a vague "
"'a chart showing revenue' with no data scores low. The data may appear as a described figure OR as a "
"table — both count.\n"
"   - diagram_score 0-100: did it recover the diagram(s)' components/labels and their relationships/flow?\n"
"   If the page has no graphs, set every graph_score to null; if no diagrams, set every diagram_score "
"to null. Grade strictly and differentiate the parsers.\n"
)


def schema(letters):
    props = {L: {"type": "object", "additionalProperties": False,
                 "properties": {"graph_score": {"type": ["integer", "null"]},
                                "diagram_score": {"type": ["integer", "null"]}},
                 "required": ["graph_score", "diagram_score"]} for L in letters}
    return {"type": "object", "additionalProperties": False,
            "properties": {
                "graphs": {"type": "array", "items": {"type": "string"}},
                "diagrams": {"type": "array", "items": {"type": "string"}},
                "scores": {"type": "object", "additionalProperties": False,
                           "properties": props, "required": list(letters)},
            }, "required": ["graphs", "diagrams", "scores"]}


def vendor_blob(rec, limit=7000):
    """Figure-grading blob: prioritize FIGURES + TABLES (where graph data lives) with
    generous per-item limits so detailed data (e.g. Landing AI / gpt-5 data points) is not
    truncated. Page body text is irrelevant to figure grading and omitted."""
    limit = BLOB_CAP
    parts = []
    for f in rec.get("figures", [])[:NFIG]:
        parts.append(f"FIGURE[{f.get('kind')}]: " + str(f.get("content", ""))[:FIG_CAP])
    for t in rec.get("tables", [])[:NTAB]:
        parts.append("TABLE: " + str(t)[:TAB_CAP])
    if not parts:
        # no figures/tables — give a hint of the text so judge can see if data is in prose
        txt = " | ".join(rec.get("ordered_texts", [])[:20])
        return ("TEXT-ONLY (no figure/table blocks): " + txt)[:limit] if txt else "(no extraction)"
    return "\n".join(parts)[:limit]


_local = threading.local()
def client():
    if not hasattr(_local, "c"): _local.c = OpenAI()
    return _local.c


def judge_page(doc, page, vendor_recs, png):
    # blind shuffle vendor -> letter (deterministic per page)
    rnd = random.Random(f"{doc}:{page}")
    order = VENDORS[:]; rnd.shuffle(order)
    letters = LETTERS[:len(order)]
    mapping = dict(zip(letters, order))  # letter -> vendor
    b64 = base64.b64encode(open(png, "rb").read()).decode()
    blocks = [PROMPT_HEAD]
    for L, vd in mapping.items():
        blocks.append(f"\n===== EXTRACTION {L} =====\n{vendor_blob(vendor_recs[vd])}")
    text = "\n".join(blocks)
    fmt = {"format": {"type": "json_schema", "name": "figure_grade", "strict": True,
                      "schema": schema(letters)}}
    content = [{"type": "input_text", "text": text},
               {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"}]
    for attempt in range(4):
        try:
            r = client().responses.create(model=MODEL, reasoning={"effort": "low"},
                                          input=[{"role": "user", "content": content}],
                                          text=fmt, max_output_tokens=4000)
            obj = json.loads(r.output_text)
            it, ot = r.usage.input_tokens, r.usage.output_tokens
            cost = (it * PRICE_IN + ot * PRICE_OUT) / 1e6
            # remap letters -> vendors
            scores = {mapping[L]: obj["scores"][L] for L in letters}
            return {"doc": doc, "page": page, "graphs": obj["graphs"],
                    "diagrams": obj["diagrams"], "scores": scores, "cost_usd": round(cost, 6)}
        except Exception as e:
            last = e; time.sleep(2 * (attempt + 1))
    return {"doc": doc, "page": page, "error": str(last), "scores": {}}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    cache_dir = os.environ.get("FIG_CACHE", "ground_truth/figure_judge")
    out_path = os.environ.get("FIG_OUT", "results/_figure_judging.json")
    key = {(e["doc"], e["page"]): e["final_label"]
           for e in json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))["pages"]}
    targets = [(d, p) for (d, p), c in key.items() if c in ("Chart/Diagram", "Mixed")]
    vend = {vd: {(r["doc"], r["page"]): r for r in json.load(open(f"results/_extract_{vd}.json"))}
            for vd in VENDORS}
    manifest = {(m["doc"], m["page"]): m["png"] for m in json.load(open(os.path.join(RENDER, "_manifest.json")))}

    os.makedirs(cache_dir, exist_ok=True)

    def task(dp):
        doc, page = dp
        cp = os.path.join(cache_dir, f"{doc}__p{page:04d}.json")
        if os.path.exists(cp):
            return json.load(open(cp))
        recs = {vd: vend[vd].get((doc, page), {}) for vd in VENDORS}
        png = os.path.join(RENDER, manifest[(doc, page)])
        res = judge_page(doc, page, recs, png)
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
    print(f"judged {len(out)} pages; errors {len(errs)}; cost ${sum(r.get('cost_usd',0) for r in out):.2f}")


if __name__ == "__main__":
    main()
