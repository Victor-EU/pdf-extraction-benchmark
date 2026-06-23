#!/usr/bin/env python3
"""Quick DPT-2 check on the 7-page insurance corpus: does the current Landing AI model
(v1/ade/parse, dpt-2-latest) extract form FIELDS where the legacy endpoint summarised dense
blocks as `figure`? Saves raw + prints a legacy-vs-DPT-2 chunk-type comparison per page.
Output: ground_truth/landingai_dpt2/raw/<png>.json
"""
import os, sys, json, time, glob, collections, requests

PARSE_URL = "https://api.va.landing.ai/v1/ade/parse"
MODEL = "dpt-2-latest"
RENDER = "ground_truth/render_full"
OUT = "ground_truth/landingai_dpt2/raw"


def key():
    for l in open(".env"):
        if l.startswith("VISION_AGENT_API_KEY="):
            return l.split("=", 1)[1].strip()


def call(png, k):
    for a in range(4):
        with open(png, "rb") as f:
            r = requests.post(PARSE_URL, headers={"Authorization": f"Bearer {k}"},
                              files={"document": (os.path.basename(png), f, "image/png")},
                              data={"model": MODEL}, timeout=180)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** a + 1); continue
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    raise RuntimeError("retries exhausted")


def main():
    os.makedirs(OUT, exist_ok=True)
    k = key()
    man = json.load(open(os.path.join(RENDER, "_manifest.json")))
    for m in man:
        png = os.path.join(RENDER, m["png"])
        raw = os.path.join(OUT, m["png"] + ".json")
        if os.path.exists(raw):
            d = json.load(open(raw))
        else:
            d = call(png, k); json.dump(d, open(raw, "w"))
        # DPT-2 chunk types
        new = collections.Counter(c.get("type", "") for c in d.get("chunks", []))
        # legacy chunk types
        legf = f"ground_truth/landingai_full/raw/{m['png']}.json"
        leg = collections.Counter()
        if os.path.exists(legf):
            leg = collections.Counter(c.get("chunk_type", "")
                                      for c in json.load(open(legf)).get("data", {}).get("chunks", []))
        ver = (d.get("metadata", {}) or {}).get("version")
        print(f"{m['doc'][:24]:26} p{m['page']}  legacy={dict(leg)}  DPT2={dict(new)}  [{ver}]")
    print(f"\nraw -> {OUT}")


if __name__ == "__main__":
    main()
