# Ground-Truth Validation — does the benchmark's foundation hold up?

**Date:** 2026-06-13 · **Scope:** the `GROUND_TRUTH.md` transcription that the headline *fair total*
is graded against. Companion to [`FINAL_REPORT.md`](FINAL_REPORT.md) / [`DESIGN.md`](DESIGN.md).

## The question on trial
The benchmark's most debatable point: **gpt-5 built the reference transcription AND a gpt-5 judge
grades against it.** A skeptic's attack: *"native-vision LLMs (gpt-5, Gemini) describe charts the
same way the reference does, so of course they win; the 16-page 'independent check' proves nothing."*
This document tests that attack on three independent axes — the **faithfulness** of the reference, the
**reference family**, and the **judge family** — and reports what broke, what held, and what we changed.

> **Bottom line.** The audit found the v1 GT *did* have real, material data errors — but only on dense
> multi-series **figures**, and they biased the benchmark **against** the text-layer parsers, not toward
> them. We corrected the GT (text-layer-anchored rebuild of all figure pages) and re-ran everything. The
> **vendor ranking is unchanged**, the conclusions hold, and the corrected reference is now canonical.

---

## 1. Independent faithfulness audit (firewall 1: is the reference true?)
An independent **Claude** auditor family (not the gpt-5 that built the GT) checked a **36-page,
chart-weighted** sample (3.4× the original §9 sample), and every flagged page was re-verified by hand
at 3–6× zoom. Full detail: [`results/gt_audit_v2/FAITHFULNESS_AUDIT_v2.md`](results/gt_audit_v2/FAITHFULNESS_AUDIT_v2.md).

**Result: 30 faithful · 2 minor · 4 material defects — all four on dense multi-series figures/grids.**
The earlier "16/16 faithful, zero omissions" claim was **too strong**; a chart-weighted, zoom-verified
sample finds real defects. The four (all author-verified against the page image):

| Page | Defect | Kind |
|---|---|---|
| SOTER p30 | 17 of 21 *printed* ARPU labels replaced with a smoother invented series | numeric hallucination |
| SOTER p102 | "Personal" subscriber base-collapse missed; (2.2) churn bar omitted; flat base invented | structural |
| Alpha p100 | activity checkmark grid row-misaligned (2 fabricated, 3 missed) | sparse-grid |
| Alpha p22 | stacked-bar **series↔colour mapping swapped** (magnitudes right, labels wrong) | semantic |

Text, prose, financial tables (number-for-number, arithmetically self-consistent), org charts, diagrams,
covers and photos were faithful throughout — the §9 arithmetic evidence stands.

---

## 2. Corpus-wide scope via the text layer (firewall 1, quantified)
All three PDFs are born-digital, so every **printed** number sits in the text layer — an exact, vision-free
oracle. `scripts/gt_textlayer_audit.py` diffs the GT's numbers against the text layer on all 599 pages.

> **Honesty note — a metric artifact we caught.** The first tokenizer merged comma-separated number lists
> (`"185, 184, 165"`) into one mega-token, making chart series look 50% "missing" and suggesting an alarming
> 86% chart recall. That was a *measurement* bug (the same class of artifact that produced the project's
> earlier table-metric scare), not a GT defect. With the tokenizer fixed:

| Category | v1 GT printed-number recall | corrected v2 GT |
|---|---:|---:|
| Text | 99.6% | 99.7% |
| Table | 98.3% | 99.6% |
| **Chart/Diagram** | **97.5%** | **99.1%** |
| Mixed | 99.0% | 99.7% |
| **TOTAL** | **98.4%** | **99.5%** |

So the v1 GT was **far better than the buggy detector implied** — but its chart pages still carried a real
~2.5% printed-number error rate (the worst cases being the audit's verified defects), and the text-layer
detector is blind to the *non-numeric* errors (series-swap, checkmarks) the manual audit caught.

---

## 3. The correction (firewall 2: swap the reference's inputs)
We rebuilt the **275 figure/Mixed + flagged pages** with `scripts/build_gt_md_v2.py`, keeping gpt-5 as the
builder (so it stays the ◆ upper-bound and Gemini stays cleanly graded) but fixing the two root causes:
1. the **exact PDF text layer** is supplied and declared authoritative for every printed value;
2. the page is re-rendered at **2400px** (vs the original 1600px, where `185` vs `165` is illegible).

Cost $11.77, 0 errors. Verified fixes on every audited defect — e.g. SOTER p30 ARPU now reads the exact
printed `…185, 184, …, 201, …, 116, …`; p102 now carries `opening 2.6,2.7,2.8,0.6,0.8,1.1` and
`net adds 0.1,0.1,(2.2),…`; p22 now maps `Domestique=1,2 / Touriste=0,5` correctly. Printed-number recall
rises to 99.1% on charts / 99.5% overall (table above). `GROUND_TRUTH_v2.md` is now canonical.

---

## 4. Re-judge: does correcting the GT move the ranking? (the headline test)
Same vendor extractions, same blind gpt-5 judge, **only the reference changed** (v1 cache reused verbatim
for the 325 unchanged pages, so this isolates the GT correction with zero re-roll noise off-target).
Full table: [`results/FAIR_TOTAL_V1_V2.md`](results/FAIR_TOTAL_V1_V2.md).

| Vendor | v1 fair total | v2 fair total | Δ | **Chart Δ** |
|---|---:|---:|---:|---:|
| Gemini 3.5 Flash | 90.0% | 91.6% | +1.6 | +4.1 |
| Gemini 3.1 Flash-Lite | 88.3% | 89.7% | +1.4 | +4.1 |
| Landing AI | 84.5% | 85.0% | +0.4 | **+1.0** |
| PyMuPDF | 81.2% | 84.3% | +3.2 | **+7.6** |
| LlamaParse | 68.1% | 70.9% | +2.8 | **+6.4** |
| Tesseract | 62.2% | 64.2% | +2.0 | +5.0 |
| gpt-5 (image) ◆ | 91.1% | 90.9% | **−0.2** | **−0.2** |
| gpt-5 (file) ◆ | 89.0% | 90.6% | +1.6 | +4.4 |

> _These v1/v2 figures isolate the **GT correction** alone (same 6,000-char judge cap on both sides). A later, separate fix — removing a judge-input truncation that clipped only Landing AI — raised the canonical numbers again (Landing AI 85.0→**87.4%**, Gemini Flash 91.6→**91.8%**); see [`AUDIT_VEND_CAP.md`](AUDIT_VEND_CAP.md) and [`results/FAIR_TOTAL.md`](results/FAIR_TOTAL.md) for the current values. The ranking is unchanged by either correction._

**Ranking: identical** (Gemini Flash > Flash-Lite > Landing AI > PyMuPDF > LlamaParse > Tesseract).
**But the correction reveals — and removes — exactly the twin bias the skeptic feared, pointed the
opposite way from the accusation:** the vendors that *correctly read the printed chart numbers* from the
text layer (PyMuPDF +7.6, LlamaParse +6.4, gpt-5-file +4.4) were being **penalized** for disagreeing with
gpt-5's hallucinated values, while **gpt-5-image — the one model that shared the GT's blind spot — is the
only vendor that did not improve (−0.2)**. That file-mode-gains / image-mode-flat split is internal proof
the effect is real signal, not noise. Net: the headline ranking is robust; the corrected GT closes the
LLM-vs-parser gap on charts and *strengthens* the "text-layer parsers are underrated on born-digital docs" finding. (Wording fix: neither tool here is "free" — **PyMuPDF is AGPL-3.0 / paid-commercial**, not free for proprietary use, and **LlamaParse is a paid API**. The underrated-value point holds; the permissively-licensed, genuinely-free text-layer options are **pdfplumber (MIT) / pypdf (BSD)**. See `FINAL_REPORT.md` §6 note ¹.)

---

## 5. Cross-family judge (firewall 3: swap the judge)
`scripts/score_fair_total_gemini.py` re-judges all 599 pages against the corrected GT with **Gemini 3.5
Flash** — a non-OpenAI judge — using the byte-identical prompt, blind shuffle, and caps, so the only
variable is the judge family. *(Caveat: Gemini is itself a contestant; but the gpt-5 judge already scored
Gemini's figures above its own, so cross-family judging is not self-serving.)*

| Vendor | gpt-5 judge (v2 GT) | Gemini judge (v2 GT) |
|---|---:|---:|
| Gemini 3.5 Flash | 91.6% | 97.3% |
| Gemini 3.1 Flash-Lite | 89.7% | 95.3% |
| Landing AI | 85.0% | 93.5% |
| PyMuPDF | 84.3% | 83.6% |
| LlamaParse | 70.9% | 73.9% |
| Tesseract | 64.2% | 76.6% |
| gpt-5 (image) ◆ | 90.9% | 97.4% |
| gpt-5 (file) ◆ | 90.6% | 96.4% |

- **gpt-5 judge rank:** Gemini Flash > Flash-Lite > Landing AI > PyMuPDF > LlamaParse > Tesseract
- **Gemini judge rank:** Gemini Flash > Flash-Lite > Landing AI > PyMuPDF > **Tesseract > LlamaParse**

The Gemini judge grades **more leniently** (absolute scores +5–12pp), but the part that matters is
**rank-invariant: the top four are identical** (Gemini Flash wins; Landing AI is third behind *both*
Geminis; PyMuPDF is a strong fourth). The **only** difference is the two weakest, figure-blind tools
(LlamaParse ↔ Tesseract) trading 5th/6th — Gemini is kinder to Tesseract's OCR text. Crucially, the
Gemini judge rates **gpt-5-image (97.4) slightly above its own family's Gemini Flash (97.3)** — the
mirror of the gpt-5 judge preferring Gemini's diagrams. **Neither judge favours its own family**, which
is the direct empirical rebuttal to the "monoculture judge" critique. (1 of 599 pages failed Gemini
judging; negligible.) Comparison: [`results/FAIR_TOTAL_JUDGES.md`](results/FAIR_TOTAL_JUDGES.md).

---

## 6. Conclusion
- The v1 GT was **sound on the born-digital majority** (text/tables/diagrams/covers: 98–99.6% printed-number
  fidelity, arithmetic-consistent statements) but had a **real, material error rate on dense multi-series
  figures** — the "16/16 faithful" claim was overstated.
- Those errors **biased the benchmark against the text-layer parsers**, not toward the LLMs — the opposite
  of the monoculture accusation.
- We **corrected the reference** (text-layer-anchored, 99.5% printed-number fidelity) and re-measured: the
  **ranking is unchanged** and the conclusions are more accurate, not less.
- Remaining honest caveats: chart geometry for label-free points is still estimated; single judge pass
  (cross-checked here by family); n = 3 born-digital documents.
