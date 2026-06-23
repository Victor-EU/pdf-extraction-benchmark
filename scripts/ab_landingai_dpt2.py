#!/usr/bin/env python3
"""A/B runner: Landing AI DPT-2 (NEW `v1/ade/parse`, model=dpt-2-latest) vs the legacy
`v1/tools/agentic-document-analysis` endpoint the benchmark currently uses.

Runs DPT-2 over a representative, chart-weighted SOTER subset (the M&A memo = LA's weakest
genre, 60% chart/diagram pages — where DPT-2's table/visual gains should show up). For each
page it captures BOTH:
  - native_md : DPT-2's top-level `markdown` (the new native output)
  - chunk_md  : markdown reconstructed from `chunks` with the SAME reducer spirit as the
                legacy collect_landingai(), so the judge can ATTRIBUTE the delta:
                  legacy(DPT-1, chunks)  -> dpt2_chunks : pure MODEL delta
                  dpt2_chunks            -> dpt2 native  : output-format delta

Auth: NEW endpoint uses `Authorization: Bearer` (legacy used `Basic`). Same VISION_AGENT_API_KEY.
Usage:  python3 scripts/ab_landingai_dpt2.py [limit]   # limit = smoke-test N pages first
Output: ground_truth/landingai_dpt2_ab/{raw/*.json, extract.json}
"""
import os, sys, json, time, re, collections, requests

PARSE_URL = "https://api.va.landing.ai/v1/ade/parse"
MODEL = "dpt-2-latest"
DOC = "SOTER - Company Presentation - vFF"
RENDER = "ground_truth/render_full"
OUT = "ground_truth/landingai_dpt2_ab"
# chart-weighted subset: counts per GT category (evenly spaced within each category)
SEL = {"Chart/Diagram": 8, "Table": 3, "Mixed": 2, "Cover/Divider": 1, "Image/Photo": 1}

TABLE_TYPES = {"table"}
FIG_TYPES = {"figure", "image", "chart", "picture"}


def api_key():
    if os.path.exists(".env"):
        for l in open(".env"):
            if l.startswith("VISION_AGENT_API_KEY="):
                v = l.split("=", 1)[1].strip()
                if v:
                    return v
    return os.environ["VISION_AGENT_API_KEY"]


def pick_pages():
    k = json.load(open("ground_truth/reconcile/final_answer_key_v3.json"))
    soter = [r for r in k["pages"] if r["doc"] == DOC]
    bycat = collections.defaultdict(list)
    for r in soter:
        bycat[r["final_label"]].append(r["page"])
    chosen = []
    for cat, n in SEL.items():
        pgs = sorted(bycat.get(cat, []))
        if not pgs:
            continue
        if n >= len(pgs):
            sel = pgs
        else:
            step = len(pgs) / n
            sel = [pgs[int(i * step)] for i in range(n)]
        chosen += [(p, cat) for p in sel]
    return sorted(set(chosen))


def clean_md(s):
    """Strip DPT-2 format noise the legacy output never had, so the judge compares CONTENT,
    not format: grounding anchors (<a id=...></a>) and figure-caption delimiters (<:: ::>)."""
    s = s or ""
    s = re.sub(r"<a id='[^']*'></a>", "", s)        # grounding cross-ref anchors
    s = s.replace("<::", "").replace("::>", "")      # figure-caption delimiters
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def reconstruct(chunks):
    """Markdown from chunks — same spirit as legacy collect_landingai (text+table+figure)."""
    parts = []
    for c in chunks or []:
        md = clean_md(c.get("markdown") or c.get("text") or "")
        if md:
            parts.append(md)
    return "\n".join(parts).strip()


def call_parse(png, key, retries=4):
    headers = {"Authorization": f"Bearer {key}"}
    last = None
    for a in range(retries):
        try:
            with open(png, "rb") as f:
                files = {"document": (os.path.basename(png), f, "image/png")}
                data = {"model": MODEL}
                t0 = time.time()
                r = requests.post(PARSE_URL, headers=headers, files=files, data=data, timeout=180)
            wall = time.time() - t0
            if r.status_code == 200:
                return r.json(), wall, None
            last = f"HTTP {r.status_code}: {r.text[:400]}"
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** a + 1)
                continue
            return None, 0, last
        except Exception as e:
            last = str(e)
            time.sleep(2 ** a + 1)
    return None, 0, last


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    key = api_key()
    raw_dir = os.path.join(OUT, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    pages = pick_pages()
    if limit:
        pages = pages[:limit]
    print(f"DPT-2 A/B over {len(pages)} SOTER pages (chart-weighted): "
          f"{[(p, c[:5]) for p, c in pages]}")
    records = []
    for page, cat in pages:
        png = os.path.join(RENDER, f"{DOC}__p{page:04d}.png")
        raw_path = os.path.join(raw_dir, f"{DOC}__p{page:04d}.png.json")
        if os.path.exists(raw_path):
            resp = json.load(open(raw_path))
            wall = resp.get("_wall")
        else:
            if not os.path.exists(png):
                print(f"  p{page} MISSING PNG {png}")
                continue
            resp, wall, err = call_parse(png, key)
            if resp is None:
                print(f"  p{page} ERROR {err}")
                continue
            resp["_wall"] = wall
            json.dump(resp, open(raw_path, "w"))
        chunks = resp.get("chunks", [])
        native = clean_md(resp.get("markdown", ""))
        chunk_md = reconstruct(chunks)
        meta = resp.get("metadata", {}) or {}
        credit = meta.get("credit_usage")
        records.append({"doc": DOC, "page": page, "cat": cat,
                        "native_md": native, "chunk_md": chunk_md,
                        "n_chunks": len(chunks), "credit": credit,
                        "wall": round(wall, 2) if wall else None})
        print(f"  p{page:<4} {cat:<14} chunks={len(chunks):<3} "
              f"native={len(native):<6} chunk_md={len(chunk_md):<6} credit={credit} {wall and round(wall,1)}s")
    json.dump(records, open(os.path.join(OUT, "extract.json"), "w"), indent=2)
    tot_credit = sum(r["credit"] for r in records if r.get("credit"))
    print(f"\nWrote {len(records)} pages -> {OUT}/extract.json  total credit={tot_credit}")


if __name__ == "__main__":
    main()
