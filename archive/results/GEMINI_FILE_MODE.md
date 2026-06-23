# Gemini native-PDF (`file`) vs rendered-image (`image`) — does the free text layer help?

Same model, same prompt, same block schema, `thinkingLevel=minimal` — only the INPUT changes: a rendered **PNG** (`image`) vs the native **1-page PDF** (`file`, from which Gemini 3.x extracts the embedded text layer *and does not bill those tokens*). The gpt-5 study found `file` wins on clean text but over-calls Text on Mixed pages and loses on figures — does Gemini behave the same?

Figure dims = a dedicated BLIND 4-way gpt-5 vision judge over these 4 configs only (122 graph pages, 103 diagram pages), separate from the canonical 8-vendor judge so those numbers are NOT directly comparable to the main matrix — read the image↔file DELTA, not the level.

> _Re-judged 2026-06-13 at no-truncation figure caps (`AUDIT_VEND_CAP.md`). Clipping here was mild and balanced image↔file (flash 18 vs 15 figures clipped; lite 1 vs 0; blob never exceeded 7000), so the verdict is unchanged — confirmed not a truncation artifact._

## The A/B matrix

| Config | Content | Numbers | Tables | Graph data | Diagram | Order τ | Cost (599pp) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemini 3.5 Flash · image | 97% | 96% | 98% | 90% | 94% | 67% | $7.12 |
| Gemini 3.5 Flash · file | 97% | 96% | 100% | 90% | 92% | 67% | $6.35 |
| Gemini 3.1 Flash-Lite · image | 96% | 95% | 94% | 85% | 81% | 67% | $1.12 |
| Gemini 3.1 Flash-Lite · file | 96% | 94% | 95% | 83% | 82% | 65% | $1.05 |

## File − image delta (per model)

| Model | ΔContent | ΔNumbers | ΔTables | ΔGraph | ΔDiagram | ΔCost |
|---|---:|---:|---:|---:|---:|---:|
| Gemini 3.5 Flash | ±0pp | ±0pp | +2pp | +1pp | -2pp | -0.77 |
| Gemini 3.1 Flash-Lite | ±0pp | -1pp | +1pp | -2pp | ±0pp | -0.07 |

## Token economics (the free-native-text claim)

| Config | mean in-tok/pg | mean out-tok/pg | mean s/pg |
|---|---:|---:|---:|
| Gemini 3.5 Flash · image | 1446 | 1078 | 6.87 |
| Gemini 3.5 Flash · file | 891 | 1029 | 5.92 |
| Gemini 3.1 Flash-Lite · image | 1446 | 1010 | 4.42 |
| Gemini 3.1 Flash-Lite · file | 891 | 1020 | 3.97 |

## Verdict

**Native-PDF input is a wash for Gemini — keep `image` mode as canonical.** Every quality dimension lands within ±1–2pp of rendered-image input (noise): Flash is effectively identical (graph +1 / diagram −2), Flash-Lite is marginally *worse* in `file` (numbers −1, graph −2, order −2) and added 2 more degenerate pages. This is the OPPOSITE of the gpt-5 image-vs-file split, where the text layer measurably helped clean text — here Gemini's native vision already saturates text/number recall (~96–97%) on born-digital PDFs, so the embedded text layer has nothing to add.

**The free-native-text claim is real but doesn't move cost.** `file` cuts input ~38% (1446→891 tok/pg) and is ~15% faster, but output tokens (~1000/pg, *unchanged*) dominate the bill at output-rate ≫ input-rate — so Flash saves only $0.77 (11%) and Flash-Lite $0.07 (6%). Native PDF is worth choosing only at high volume, and only for Flash (Flash-Lite `file` is slightly worse and flakier). For this benchmark the canonical 8-vendor matrix stays on `image` mode.

## Degenerate pages

  - Gemini 3.5 Flash · image: 20190308_Projet_Alpha_Restitution p5 (degenerate/empty)
  - Gemini 3.1 Flash-Lite · image: IAR_FY25_EN p103 (degenerate/empty)
  - Gemini 3.1 Flash-Lite · file: IAR_FY25_EN p14 (degenerate/empty)
  - Gemini 3.1 Flash-Lite · file: IAR_FY25_EN p49 (degenerate/empty)

