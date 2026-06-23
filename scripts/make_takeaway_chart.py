#!/usr/bin/env python3
"""The single takeaway graph: capture quality vs trustworthiness.
Y = structure-aware fair total (how much correctly-bound info captured, gpt-5 judge, HEADLINE).
X = unsupported rate (fabrication / how much it invents, gpt-5 judge) — LEFT is safer.
All numbers verified against results/_fair_total_judging.json (2026-06-23)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# (label, quality Y, unsupported X, family, cost_note, ref?, text-x, text-y, ha)
D = [
    ("Gemini 3.5 Flash",      89.0,  8.3, "vision", "$7.12",  False,  4.6, 92.2, "center"),
    ("gpt-5 (image) ◆",  87.9,  8.8, "ref",    "$13.82", True,   9.7, 91.6, "left"),
    ("gpt-5 (file) ◆",   86.9,  8.5, "ref",    "$12.54", True,  11.6, 90.0, "left"),
    ("Landing AI (DPT-2)",    86.0, 10.6, "vision", "paid",   False, 13.0, 87.4, "left"),
    ("LlamaParse (agentic)",  85.5, 10.2, "vision", "paid",   False, 13.0, 83.8, "left"),
    ("Gemini 3.1 Flash-Lite", 85.8,  7.8, "vision", "$1.12",  False,  2.9, 82.4, "left"),
    ("Mistral OCR 4",         80.0, 19.3, "vision", "~$3",    False, 16.2, 75.5, "left"),
    ("PyMuPDF",               68.3,  5.4, "text",   "$0*",    False,  6.1, 68.3, "left"),
    ("LiteParse",             62.2,  8.2, "text",   "$0",     False,  9.0, 62.2, "left"),
    ("Tesseract",             51.8, 15.0, "text",   "$0",     False, 13.4, 51.8, "right"),
]

VIS = "#1f77b4"   # AI vision tools
TXT = "#b5651d"   # text-layer tools
REF = "#9aa0a6"   # gpt-5 reference (built the ground truth)

fig, ax = plt.subplots(figsize=(11.5, 7.6))
ax.set_xlim(2.5, 22)
ax.set_ylim(48, 93.5)

# "safe & accurate" corner: high quality + low fabrication
xmax_frac = (11 - 2.5) / (22 - 2.5)
ax.axhspan(83, 93.5, xmin=0, xmax=xmax_frac, color="#e9f6ea", zorder=0)
ax.text(2.8, 84.4, "SAFE & ACCURATE\nhigh capture · low invention",
        fontsize=9, color="#2e7d32", weight="bold", va="center")

for label, y, x, fam, cost, ref, tx, ty, ha in D:
    color = {"vision": VIS, "text": TXT, "ref": REF}[fam]
    marker = "^" if fam == "text" else "o"
    face = "none" if ref else color
    ax.scatter(x, y, s=240, marker=marker, facecolors=face, edgecolors=color,
               linewidths=2.3, zorder=6)
    if label.startswith("Mistral"):  # red warning ring on the fabrication outlier
        ax.scatter(x, y, s=620, marker="o", facecolors="none", edgecolors="#c62828",
                   linewidths=2.3, linestyle=(0, (2, 1.5)), zorder=5)
    bold = "bold" if label == "Gemini 3.5 Flash" else "normal"
    ax.annotate(f"{label}  ({cost})", (x, y), (tx, ty), ha=ha, va="center",
                fontsize=9.4, color="#1a1a1a", weight=bold, zorder=7,
                arrowprops=dict(arrowstyle="-", color="#999", lw=0.8,
                                shrinkA=2, shrinkB=8))

ax.set_xlabel("Fabrication risk  —  % of output unsupported by the page   "
              "(← safer · riskier →)", fontsize=11)
ax.set_ylabel("Capture quality  —  structure-aware fair total, %   "
              "(higher = more correctly-bound information)", fontsize=11)
ax.set_title("PDF extraction for finance: capture quality and trustworthiness are SEPARATE axes",
             fontsize=13.5, weight="bold", pad=12)
ax.grid(True, alpha=0.25)

leg = [
    Line2D([0],[0], marker="o", color="w", markerfacecolor=VIS, markersize=12, label="AI vision tools"),
    Line2D([0],[0], marker="^", color="w", markerfacecolor=TXT, markersize=12, label="Text-layer tools (cheap, no vision)"),
    Line2D([0],[0], marker="o", color="w", markerfacecolor="none", markeredgecolor=REF, markeredgewidth=2, markersize=12, label="gpt-5 ◆ (reference / upper bound)"),
    Line2D([0],[0], marker="o", color="w", markerfacecolor="none", markeredgecolor="#c62828", markeredgewidth=2, markersize=14, label="fabrication outlier"),
]
ax.legend(handles=leg, loc="lower right", fontsize=9.5, framealpha=0.96)

cap = ("599 pages of real finance documents (annual report, consulting deck, M&A memo) · 10 tools · blind gpt-5 judge.   "
       "*PyMuPDF runs free but is AGPL-licensed (paid for commercial use).\n"
       "Takeaway: the cheap default (Gemini 3.5 Flash) is already in the safe corner; text-layer tools are free but lose structure; "
       "Mistral reads charts but is pushed right by inventing what it can’t read.")
fig.text(0.5, 0.008, cap, ha="center", fontsize=8.5, color="#444")
fig.subplots_adjust(bottom=0.155, top=0.93, left=0.082, right=0.975)
out = "results/TAKEAWAY_quality_vs_trust.png"
fig.savefig(out, dpi=180)
print("wrote", out)
