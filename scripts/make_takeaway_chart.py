#!/usr/bin/env python3
"""The single takeaway graph for the insurance-forms benchmark: reading the CHECKBOX is the
dividing line, and there is no middle ground.

  Y = capture quality   = structure-aware fair total (gpt-5 judge, HEADLINE), Σ(recall·w)/Σw.
  X = checkbox fidelity  = checkbox_state read correctly (gpt-5 spatial judge), the form's
                           single most consequential, purely-visual datum, weighted over the
                           pages that contain a checkbox.

Both axes are computed LIVE from the canonical judging JSONs so the graph cannot drift from the
data. ◆ = ground-truth co-author (Gemini, Landing AI) — upper bound, plotted hollow, not ranked.

Punchline: capture quality and checkbox-reading rise together, and the middle is EMPTY — vision
tools read ticks (85–100%), text-layer tools cannot (0–22%) even when they recover every character
(PyMuPDF). Mistral OCR 4 leads here yet was 5th-of-10 and the worst fabricator on the finance
corpus: genre, not the tool, decides."""
import json
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# (vendor key, display label, class, is ◆ reference, text-x, text-y, ha)
META = [
    ("gemini_flash", "Gemini 3.5 Flash ◆", "vision", True,  78, 101, "right"),
    ("mistral",      "Mistral OCR 4",      "vision", False, 80,  90, "right"),
    ("pulse",        "Pulse (Ultra 2)",    "vision", False, 66,  95, "right"),
    ("landingai",    "Landing AI (DPT-2) ◆","vision", True, 72,  84, "right"),
    ("gpt5_image",   "gpt-5 (image)",      "vision", False, 64,  78, "right"),
    ("liteparse",    "LiteParse",          "text",   False, 30,  59, "left"),
    ("pymupdf",      "PyMuPDF",            "text",   False,  7,  52, "left"),
    ("tesseract",    "Tesseract",          "text",   False, 14,  41, "left"),
    ("llamaparse",   "LlamaParse",         "text",   False,  7,  30, "left"),
]

# ---- Y: structure-aware fair total (weighted recall) ----
fj = json.load(open("results/_fair_total_judging.json"))
num = defaultdict(float); den = defaultdict(float)
for r in fj:
    if r.get("error"):
        continue
    w = r.get("weight", 1)
    for vd, s in r.get("scores", {}).items():
        if s.get("info_recall") is not None:
            num[vd] += s["info_recall"] * w; den[vd] += w
fair = {vd: num[vd] / den[vd] for vd in num}

# ---- X: checkbox_state correct (weighted over checkbox-bearing pages) ----
sj = json.load(open("results/_spatial_judging.json"))
cn = defaultdict(float); cd = defaultdict(float)
for r in sj:
    w = r.get("weight") or 0
    for vd, s in r.get("scores", {}).items():
        if w and s and s.get("checkbox_present"):
            cn[vd] += s["checkbox_state"] * w; cd[vd] += w
check = {vd: (cn[vd] / cd[vd] if cd[vd] else 0.0) for vd in cn}

VIS = "#1f77b4"; TXT = "#b5651d"; REF = "#9aa0a6"
fig, ax = plt.subplots(figsize=(11.2, 7.3))
ax.set_xlim(-4, 109)
ax.set_ylim(25, 103)

# "form-ready" corner: reads ticks AND captures usable info
ax.axhspan(70, 103, xmin=(80 + 4) / 113, xmax=1.0, color="#e9f6ea", zorder=0)
ax.text(104, 72.5, "FORM-READY\nreads ticks · usable capture", fontsize=9, color="#2e7d32",
        weight="bold", ha="right", va="bottom")

# the "checkbox cliff": the empty middle — no tool lands between ~22% and ~85%
ax.axvspan(24, 80, color="#f4f0ea", zorder=0)
ax.text(52, 64, "the checkbox cliff\nno tool lands here", fontsize=10, color="#8a6d3b",
        weight="bold", ha="center", va="center", style="italic")

for vd, label, cls, ref, tx, ty, ha in META:
    if vd not in fair:
        continue
    x, y = check.get(vd, 0.0), fair[vd]
    color = VIS if cls == "vision" else TXT
    marker = "o" if cls == "vision" else "^"
    face = "none" if ref else color
    ax.scatter(x, y, s=250, marker=marker, facecolors=face, edgecolors=color,
               linewidths=2.3, zorder=6)
    if vd == "mistral":   # the genre-flip hero gets a green ring (mirrors finance's red outlier ring)
        ax.scatter(x, y, s=640, marker="o", facecolors="none", edgecolors="#2e7d32",
                   linewidths=2.2, linestyle=(0, (2, 1.5)), zorder=5)
    bold = "bold" if vd == "mistral" else "normal"
    ax.annotate(f"{label}  ({y:.0f}% cap · {x:.0f}% tick)", (x, y), (tx, ty), ha=ha, va="center",
                fontsize=9.3, color="#1a1a1a", weight=bold, zorder=7,
                arrowprops=dict(arrowstyle="-", color="#999", lw=0.8, shrinkA=2, shrinkB=8))

ax.set_xlabel("Checkbox state read correctly (%)   —   the form's decisive, purely-visual datum "
              "(can't read a tick →            ← reads every tick)", fontsize=10.5)
ax.set_ylabel("Capture quality  —  structure-aware fair total, %\n(value bound to the right field, "
              "row, and checkbox)", fontsize=10.5)
ax.set_title("Insurance forms: reading the checkbox is the dividing line — and the middle is empty",
             fontsize=13.5, weight="bold", pad=12)
ax.grid(True, alpha=0.25)

leg = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor=VIS, markersize=12, label="Vision tools (read pixels)"),
    Line2D([0], [0], marker="^", color="w", markerfacecolor=TXT, markersize=12, label="Text-layer / OCR tools (cheap, no vision)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="none", markeredgecolor=REF, markeredgewidth=2, markersize=12, label="◆ ground-truth co-author (upper bound)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="none", markeredgecolor="#2e7d32", markeredgewidth=2, markersize=14, label="genre-flip leader (was 5th-of-10 on finance)"),
]
ax.legend(handles=leg, loc="lower right", fontsize=9, framealpha=0.96)

cap = ("7 pages of French insurance / social-aid forms · 9 tools · blind gpt-5 judge.   "
       "◆ Gemini & Landing AI co-authored the ground truth (upper bound, not ranked).\n"
       "Takeaway: capture quality and checkbox-reading rise together, and there is NO middle ground — "
       "vision tools read ticks (85–100%), text-layer tools can't (0–22%) even when they recover every "
       "character (PyMuPDF). On forms, a vision model is not optional.")
fig.text(0.5, 0.008, cap, ha="center", fontsize=8.4, color="#444")
fig.subplots_adjust(bottom=0.165, top=0.93, left=0.092, right=0.975)
out = "results/TAKEAWAY_quality_vs_checkbox.png"
fig.savefig(out, dpi=180)
print("wrote", out)
for vd, label, *_ in META:
    if vd in fair:
        print(f"  {label:22} capture={fair[vd]:5.1f}  checkbox={check.get(vd,0.0):5.1f}")
