#!/usr/bin/env python3
"""Landing AI Agentic Document Extraction pass over sample pages.

Calls the ADE endpoint per rendered page image, saves raw JSON, and reduces the
typed chunks to a dominant 6-category label (one of three ground-truth votes).
"""
import os, sys, json, time, glob
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

ENDPOINT = "https://api.va.landing.ai/v1/tools/agentic-document-analysis"
CATS = ["Text", "Table", "Chart/Diagram", "Mixed", "Cover/Divider", "Image/Photo"]

TEXT_TYPES = {"text", "title", "list", "marginalia", "page_header", "page_footer",
              "key_value", "form", "caption"}
TABLE_TYPES = {"table"}
FIG_TYPES = {"figure", "image", "chart", "picture"}

PHOTO_KW = ["photo", "photograph", "picture of", "headshot", "portrait", "person",
            "people", "building", "landscape", "scenery", "silhouette", "aerial"]
CHART_KW = ["chart", "graph", "plot", "diagram", "flow", "axis", "bar ", "pie",
            "line graph", "schematic", "map", "timeline", "matrix", "funnel",
            "histogram", "scatter", "waterfall", "gantt"]


def box_area(box):
    try:
        return max(0.0, (box["r"] - box["l"])) * max(0.0, (box["b"] - box["t"]))
    except Exception:
        return 0.0


def reduce_label(data):
    chunks = data.get("chunks", []) or []
    areas = {"text": 0.0, "table": 0.0, "figure": 0.0}
    fig_text = []
    has_title = has_marginalia = False
    n_logo = 0
    for c in chunks:
        ct = c.get("chunk_type", "")
        a = 0.0
        for g in c.get("grounding", []) or []:
            if g.get("box"):
                a += box_area(g["box"])
        txt = (c.get("text") or "")
        if ct in TABLE_TYPES:
            areas["table"] += a
        elif ct in FIG_TYPES:
            areas["figure"] += a
            fig_text.append(txt.lower())
            if "logo" in txt.lower()[:30]:
                n_logo += 1
        else:  # text-ish
            areas["text"] += a
            if ct == "title":
                has_title = True
            if ct == "marginalia":
                has_marginalia = True

    total = sum(areas.values())
    # disambiguate figure -> chart vs photo from summaries
    figblob = " ".join(fig_text)
    photo_score = sum(figblob.count(k) for k in PHOTO_KW)
    chart_score = sum(figblob.count(k) for k in CHART_KW)
    figure_is_photo = photo_score > chart_score

    detail = dict(areas={k: round(v, 3) for k, v in areas.items()},
                  total=round(total, 3), photo_score=photo_score,
                  chart_score=chart_score, n_chunks=len(chunks),
                  n_logo=n_logo)

    # Cover/Divider: sparse page, dominated by title/logo/marginalia, little real text
    if total < 0.30 and areas["table"] < 0.05:
        if areas["figure"] >= 0.15 and not figure_is_photo and chart_score == 0:
            # a small figure that's a logo/branding on an otherwise empty page
            if n_logo > 0 or (has_title or has_marginalia):
                return "Cover/Divider", detail
        if has_title or has_marginalia or areas["text"] < 0.12:
            return "Cover/Divider", detail

    if total <= 0:
        return "Cover/Divider", detail

    # dominant bucket
    ranked = sorted(areas.items(), key=lambda kv: -kv[1])
    top_k, top_v = ranked[0]
    second_v = ranked[1][1]

    # Mixed: top two comparable and both meaningful
    if second_v >= 0.18 and top_v > 0 and (second_v / top_v) >= 0.6:
        return "Mixed", detail

    if top_k == "table" and top_v >= 0.18:
        return "Table", detail
    if top_k == "figure":
        if top_v >= 0.55 and areas["text"] < 0.15:
            return ("Image/Photo" if figure_is_photo else "Chart/Diagram"), detail
        return ("Image/Photo" if figure_is_photo else "Chart/Diagram"), detail
    # text dominant
    return "Text", detail


def call_ade(img_path, api_key, retries=4):
    headers = {"Authorization": f"Basic {api_key}"}
    last_err = None
    for attempt in range(retries):
        try:
            with open(img_path, "rb") as f:
                files = {"image": (os.path.basename(img_path), f, "image/png")}
                t0 = time.time()
                resp = requests.post(ENDPOINT, headers=headers, files=files, timeout=180)
            wall = time.time() - t0
            if resp.status_code == 200:
                return resp.json(), wall, None
            last_err = f"HTTP {resp.status_code}: {resp.text[:200]!r}"
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt + 1)
                continue
            return None, 0, last_err
        except Exception as e:
            last_err = str(e)
            time.sleep(2 ** attempt + 1)
    return None, 0, last_err


def main():
    render_dir = sys.argv[1] if len(sys.argv) > 1 else "ground_truth/render"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "ground_truth/landingai"
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    raw_dir = os.path.join(out_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    api_key = os.environ["VISION_AGENT_API_KEY"]

    manifest = json.load(open(os.path.join(render_dir, "_manifest.json")))

    def work(item):
        png = item["png"]
        img = os.path.join(render_dir, png)
        raw_path = os.path.join(raw_dir, png + ".json")
        if os.path.exists(raw_path):  # resume
            data = json.load(open(raw_path))
            wall = data.get("_wall")
        else:
            resp, wall, err = call_ade(img, api_key)
            if resp is None:
                return dict(**item, la_label="ERROR", error=err)
            resp["_wall"] = wall
            json.dump(resp, open(raw_path, "w"))
            data = resp
        d = data.get("data", {})
        label, detail = reduce_label(d)
        ms = (data.get("metadata", {}) or {}).get("processing_time_ms")
        return dict(doc=item["doc"], page=item["page"], png=png,
                    det_label=item.get("det_label"), la_label=label,
                    la_detail=detail, processing_time_ms=ms,
                    wall_s=round(wall, 2) if wall else None)

    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(work, it): it for it in manifest}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            tag = r.get("la_label")
            print(f"  {r['doc'][:30]:<30} p{r['page']:<4} la={tag}")

    results.sort(key=lambda r: (r["doc"], r["page"]))
    json.dump(results, open(os.path.join(out_dir, "labels.json"), "w"), indent=2)
    # timing/cost summary
    times = [r["processing_time_ms"] for r in results if r.get("processing_time_ms")]
    walls = [r["wall_s"] for r in results if r.get("wall_s")]
    errs = [r for r in results if r.get("la_label") == "ERROR"]
    print(f"\nDone: {len(results)} pages, {len(errs)} errors")
    if times:
        print(f"  server processing_time_ms: mean={sum(times)/len(times):.0f} "
              f"min={min(times)} max={max(times)}")
    if walls:
        print(f"  wall_s per call: mean={sum(walls)/len(walls):.2f}")
    print("  labels.json written")


if __name__ == "__main__":
    main()
