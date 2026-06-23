# Fair total — cross-family judge robustness (gpt-5 judge vs Gemini judge)

> **These are content-recall-era numbers (superseded as the headline 2026-06-14).** The canonical
> headline is now the **structure-aware** fair total ([`../STRUCTURE_AWARE_SCORING.md`](../STRUCTURE_AWARE_SCORING.md));
> the cross-family robustness shown here holds under it too — the structure change is identical
> across both judge families (PyMuPDF 84→68 under each). The numbers below are the content-recall
> rubric, retained for the judge-agreement analysis.

Both judges grade the **same vendor extractions** against the **same corrected v2 ground truth**, with
the **byte-identical prompt, blind A–H shuffle, and text caps** (`score_fair_total.py` vs
`score_fair_total_gemini.py`). The only variable is the **judge model family**. This isolates whether the
benchmark's conclusions depend on using an OpenAI judge. *(Numbers below are the corrected, no-truncation
run — `VEND_CAP = GT_CAP = 16000`; see `AUDIT_VEND_CAP.md`.)*

| Vendor | gpt-5 judge | Gemini 3.5 Flash judge | Δ (Gem−gpt5) |
|---|---:|---:|---:|
| Gemini 3.5 Flash | 91.8% | 97.3% | +5.5 |
| **LlamaParse** (agentic) | **89.6%** | **95.9%** | +6.3 |
| Gemini 3.1 Flash-Lite | 89.9% | 95.3% | +5.4 |
| Landing AI | 87.4% | 95.5% | +8.1 |
| PyMuPDF | 84.2% | 83.7% | −0.5 |
| Tesseract | 63.8% | 76.7% | +12.9 |
| gpt-5 (image) ◆ | 91.3% | 97.3% | +6.0 |
| gpt-5 (file) ◆ | 91.0% | 96.4% | +5.4 |

> LlamaParse is at its canonical **`agentic` tier** (`AUDIT_LLAMAPARSE_MODE.md`); weights held fixed at the
> canonical values so its row is comparable to the others (the original `accurate`-tier scores were 71.1 / 74.1).

**Ranking (clean vendors)**
- gpt-5 judge: **Gemini Flash > Flash-Lite ≈ LlamaParse > Landing AI > PyMuPDF** > Tesseract
- Gemini judge: **Gemini Flash > LlamaParse ≈ Landing AI ≈ Flash-Lite > PyMuPDF** > Tesseract

**Reading.** The Gemini judge is a more lenient grader (absolute scores +5–13pp, with Tesseract's OCR text
treated most generously), so absolute numbers are not comparable across judges — but **Gemini 3.5 Flash is
#1 clean under both**, and the top tier is stable. Below it, **LlamaParse-agentic, Flash-Lite and Landing AI
form a tight 2nd–4th cluster** (within ~2.5pp under either judge), their exact order judge-dependent. Both
judges agree LlamaParse-agentic sits in this top cluster, far above the pure text-layer parsers.
**Neither judge favours its own family**: the Gemini judge scores gpt-5-image (97.3) level with its own
Gemini Flash (97.3), mirroring the gpt-5 judge's habit of scoring Gemini's diagrams above its own. The
"the judge is gpt-5, so LLMs win" critique does not survive the swap.

*Caveat:* Gemini is itself a contestant, so its rows are read with the same care as gpt-5's ◆ rows; the
value here is the **rank stability**, not Gemini's absolute self-score. 1/599 pages (IAR p129) fails
Gemini judging in both the pre- and post-fix runs and is excluded.
