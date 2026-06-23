# Landing AI re-benchmarked on DPT-2 — full corpus, both judge families (2026-06-15)

## Why
The benchmark scored Landing AI via the **legacy** endpoint
`v1/tools/agentic-document-analysis` (the deprecated `agentic-doc` library's endpoint): no model
parameter, pre-DPT-2. Landing AI's current stack is `v1/ade/parse` with `model=dpt-2-latest`
(library `landingai-ade`; `agentic-doc` is now marked legacy). So every "Landing AI" number in the
headline reflected a superseded model. This re-benchmark replaces it with **DPT-2**
(served version `dpt-2-20260410`). This is the **7th** "a measurement choice deflated Landing AI"
finding in this project (after VEND_CAP, the table-presence metric, the LlamaParse-tier comparator,
the `##`-split truncation, the PyMuPDF structure inflation, the deterministic-scoring POC).

## What changed (and what deliberately did NOT)
- **Endpoint + model only.** Same per-page PNG input from `ground_truth/render_full` as the legacy
  benchmark. An A/B (`ground_truth/landingai_dpt2_ab/RESULTS.md`) established that for DPT-2 **PNG
  input beats native-PDF-page input** (PNG→PDF −7.2±1.3pp over 3 replicates; DPT-2 is a vision
  model and the slides' jumbled PDF text-layer reading order hurt it), and that the native-markdown
  format adds ~0 over chunk-reconstruction. So the only capability captured is **the model**.
- **Same reducer.** `collect_landingai_dpt2()` reduces DPT-2 chunks (`type`/`markdown`) exactly as
  `collect_landingai()` reduced legacy chunks (`chunk_type`/`text`) — table/figure/text buckets,
  figure-embedded-table detection — so the only judged difference is content quality, not
  representation. DPT-2 format noise (`<a id>` grounding anchors, `<:: ::>` figure delimiters) is
  stripped.
- **Byte-identical judging.** Re-judged with the canonical scorers via an `LA_DPT2` env hook on
  `build_vendor_md.load_pages` that serves the `landingai` slot from the DPT-2 extract. Same seed,
  same shuffle, same 8-vendor lineup, same 16k caps, **same prompts except Landing AI's extraction
  block.** Both families: gpt-5 (`score_fair_total_structure.py`) and Gemini 3.5 Flash
  (`score_fair_total_structure_gemini.py`), structure-aware (headline) **and** the content-recall
  diagnostic (`score_fair_total.py`, gpt-5).

## Splice validity (the controlled-swap check)
Because only LA's block changed, the other 7 vendors' scores must be stable. Per-page judge
variance is large and irrelevant (±20-25pp, measured in the A/B replicate study); what must hold is
**aggregate** stability. It does, overwhelmingly:

| | worst untouched-vendor aggregate drift | mean |
|---|---|---|
| gpt-5 | 1.09pp (gpt5_file) | 0.38pp |
| Gemini | 0.52pp (tesseract) | 0.23pp |

So swapping legacy-LA for DPT-2-LA does **not** systematically move any other vendor — the judge
grades absolutely vs ground truth, and the LA delta is a clean, controlled measurement. DPT-2's LA
scores were spliced into LA's slot of the canonical judging JSONs (legacy archived in
`results/legacy_la_archive/`); the other 7 vendors keep their canonical scores; page weights are
GT-determined (mean |Δweight| 0.33/0.22) and kept canonical.

## Result — Landing AI, legacy → DPT-2 (structure-aware fair total)

| scope | gpt-5 legacy → DPT-2 | Gemini legacy → DPT-2 |
|---|---|---|
| **Corpus** | 81.4 → **86.0  (+4.6)** | 92.6 → **93.9  (+1.3)** |
| Alpha (FR consulting) | 73.5 → 80.9  (+7.3) | 89.5 → 91.7  (+2.2) |
| IAR (annual report) | 91.0 → 92.7  (+1.7) | 96.2 → 97.1  (+0.9) |
| SOTER (M&A memo, chart-heavy) | 71.0 → 78.3  (+7.3) | 89.1 → 90.1  (+0.9) |
| **unsupported** (lower=better) | 17.6 → **11.2  (−6.4)** | 4.1 → 3.4  (−0.7) |

Both judge families agree on direction and the bigger-on-harder-genres pattern (largest gains on
the chart-heavy memo and the dense FR consulting deck; annual report already near-saturated). DPT-2
raises recall **and** cuts hallucination/misbinding.

## Headline impact (gpt-5 judge — the discriminating one)
**Landing AI moves from a clear 4th into a tie for 2nd among real vendors**, and from "middle tier,
highest padding" to "high-quality tier, near-best fidelity":

| Vendor | Fair total (was → now) | Structure gap | Unsupported |
|---|---|---|---|
| Gemini 3.5 Flash | 89 | −3 | 8% |
| **Landing AI** | **81 → 86** | **−6 → −3** | **17% → 11%** |
| Gemini 3.1 Flash-Lite | 86 | −4 | 8% |
| LlamaParse (agentic) | 86 | −4 | 10% |
| PyMuPDF | 68 | −16 | 5% |
| Tesseract | 52 | −12 | 15% |

By page category, DPT-2 Landing AI is now **best-in-class on Image/Photo (88%)**, joint-strong on
Table (86%) and Mixed (90%), and 2nd among real vendors on Chart (78%, ahead of LlamaParse 76).
Two prior FINAL_REPORT claims are now **false** and corrected: LA is no longer the "highest padding"
vendor (Tesseract 15% > LA 11%), and its structure gap is no longer "−6 / middle" but −3, tied with
the best structure-preservers. **Gemini 3.5 Flash remains the overall #1** on both families and all
three genres.

## Cost (this re-benchmark)
DPT-2 parse: 599 pages × 3 credits = **~1,797 Landing AI credits**, 0 errors. Re-judging:
gpt-5 structure $12.05 + Gemini structure $7.27 + gpt-5 content $12.33 = **$31.65**.

## Reproduce
```
python3 scripts/landingai_dpt2_full.py 6                      # parse 599 PNGs via v1/ade/parse
python3 scripts/collect_extractions.py landingai_dpt2         # -> results/_extract_landingai_dpt2.json
LA_DPT2=1 FT_CACHE=ground_truth/fair_total_structure_judge_dpt2        FT_OUT=results/_fair_total_judging_dpt2.json        python3 scripts/score_fair_total_structure.py 8
LA_DPT2=1 FT_CACHE=ground_truth/fair_total_structure_gemini_dpt2       FT_OUT=results/_fair_total_judging_gemini_v2_dpt2.json python3 scripts/score_fair_total_structure_gemini.py 6
LA_DPT2=1 FT_CACHE=ground_truth/fair_total_judge_content_dpt2          FT_OUT=results/_fair_total_judging_content_dpt2.json   python3 scripts/score_fair_total.py 8
python3 scripts/splice_dpt2.py --splice                       # validate (aggregate gate) + splice
python3 scripts/fair_total_report.py && python3 scripts/by_document.py   # regenerate headline
```
Legacy LA judging archived in `results/legacy_la_archive/`. NOT re-run here: the element-level eval
(6129 typed elements) and the figure/diagram eval — separate, larger re-judges; LA's numbers there
remain legacy until re-run (flagged for follow-up).
