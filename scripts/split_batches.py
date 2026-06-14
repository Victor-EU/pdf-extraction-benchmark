#!/usr/bin/env python3
"""Split the full render manifest into per-subagent batch files (no doc crossing)."""
import json, os, sys, math

BATCH = int(sys.argv[1]) if len(sys.argv) > 1 else 30
render_dir = "ground_truth/render_full"
out_dir = os.path.join(render_dir, "batches")
os.makedirs(out_dir, exist_ok=True)

manifest = json.load(open(os.path.join(render_dir, "_manifest.json")))
by_doc = {}
for m in manifest:
    by_doc.setdefault(m["doc"], []).append(m)

batches = []
for doc, pages in by_doc.items():
    pages.sort(key=lambda x: x["page"])
    for i in range(0, len(pages), BATCH):
        batches.append(pages[i:i + BATCH])

idx = []
for n, b in enumerate(batches, 1):
    fn = f"batch_{n:02d}.json"
    json.dump(b, open(os.path.join(out_dir, fn), "w"), indent=2)
    idx.append(dict(batch=fn, doc=b[0]["doc"], pages=f"{b[0]['page']}-{b[-1]['page']}", n=len(b)))

json.dump(idx, open(os.path.join(out_dir, "_index.json"), "w"), indent=2)
print(f"{len(batches)} batches (size {BATCH}) -> {out_dir}")
for it in idx:
    print(f"  {it['batch']}  {it['doc'][:34]:<34} p{it['pages']:<10} ({it['n']})")
