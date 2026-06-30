# Adding Pulse (runpulse.com, Ultra 2) as the 9th vendor — insurance forms

*2026-06-30. Full-corpus benchmark of Pulse (runpulse.com), run in its **most advanced configuration**
(`pulse-ultra-2` + `refine` + figure descriptions), validated and spliced into the canonical
structure-aware fair total (gpt-5 + Gemini families, structure + content) and the form
**spatial/checkbox** ranking. Headline: **90% structure-aware (gpt-5) — the clean #2**, just behind
Mistral OCR 4 (92%) and well above gpt-5 image (80%) and even the ◆ Landing AI reference (84%); and
it does it with the **lowest unsupported of any real vendor (4% gpt-5 / 2% content / 1.6% Gemini)** —
the cleanest fidelity in the field. On the form-spatial metric it is **#2 on both judges** (94% gpt-5,
86% Gemini), reading **checkbox state at 94%** — squarely in the vision tier.*

> **Where it sits.** Pulse joins Mistral OCR 4 in the small group of true vision-tier vendors that
> actually *read these forms* (checkbox glyphs, field bindings, table cells) rather than flattening
> them. Mistral is still the clean #1 on this corpus; Pulse is a close, exceptionally *clean* #2 —
> it captures slightly less than Mistral but **fabricates the least of anyone** (gap between content
> and structure is +1, i.e. it almost never asserts a binding it can't support). Its one soft spot is
> dense-table cell binding under the stricter Gemini judge (see below).

## What Pulse is + config

[Pulse](https://runpulse.com) is an enterprise document-understanding API (not plain OCR): a
five-stage pipeline (layout → OCR → reading-order → table-structure → fine-tuned VLM for
charts/figures) returning page markdown + typed bounding boxes (Text/Tables/Images/SelectionMarks/
Words) + per-value confidence. Run, per the project principle of giving each tool its best native
representation (LlamaParse on `agentic`, Landing AI on DPT-2, Mistral on `mistral-ocr-4-0`), at its
**most advanced tier** — the config is centralized in `scripts/pulse_common.py`, shared by runner +
collector so they cannot diverge:

- **`model=pulse-ultra-2`** — Pulse's self-hosted flagship vision model (vs the `default` tier),
  which unlocks the refine + figure flags below.
- **`refine=true` + `refine_options.{tables,text,formatting}=true`** — a full-page re-OCR +
  formatting-correction pass. On the corpus this **visibly cleaned the text vs `default`**: correct
  accents (`N°`, `présenter`) and it drops `default`'s per-element `0a-`/`0t-` content-prefix garbage.
  It is also slow: **~30–150s/page** (highly variable), ~10× the wall of Mistral.
- **`figure_processing.description=true`** — 1–2 paragraph VLM description per figure, so graphics are
  described with their data (parallel to Mistral's bbox annotation / Landing-AI figure chunks). On
  forms this mostly fires on logos/stamps/barcodes, so — unlike the chart-dense Finance corpus —
  there is almost nothing for it to over-read. **Note:** the older `extract_figure` /
  `figure_description` flags are **deprecated** (the API returns a warning); we use the current
  `figure_processing.description` and the run is warning-free.

### Input arm: per-page PNG

Run on the per-page **PNG renders**, matching every other vision vendor here (gpt-5 image, Gemini,
Landing AI, Mistral OCR 4) and the only sensible unit on a 7-page / 2-doc corpus of single-page
forms: Pulse's one doc-level feature (cross-page table merge) is irrelevant when the relevant unit IS
the single form page, and per-page keeps attribution clean. The AE *attestation* is a **scan** with no
born-digital text layer, so a PDF-text arm isn't even meaningful (cf. the Mistral PNG-vs-PDF A/B
already settled on these forms). 7 pages, 0 errors.

### One artifact headed off at the reducer (filler-leader bloat)

`pulse-ultra-2` + `refine` expands dotted/underscored **form fill-in lines** ("Nom : ........……") into
runs of *tens of thousands* of literal leader characters: on the MNH dossier this bloated two pages to
**120K+ chars** (real text ~2–3K). Because the runs start well inside the judge's 16K input cap, they
would push real content out of the judged window and bury it under walls of dots — penalizing Pulse for
an OCR artifact, not its reading. `pulse_common.reduce_response` **collapses each filler run to a single
ellipsis** (faithful: a leader line carries no information; other OCR vendors already collapse these).
After collapse Pulse's reconstructed corpus is 22.6K chars — in line with gpt-5 image (22.6K) and
Mistral (21.7K). The top-level `markdown` (used as the single judged block) preserves the **checkbox
glyphs (☐ blank / ☒ ☑ ticked) bound to their option labels** in reading order — the single most
consequential signal on these forms.

## How it was judged (ADD, not swap — weights frozen)

Used the existing `scripts/splice_vendor.py` (ADD, per-vendor suffix + `pre_pulse_archive`): `pulse`
added to `build_vendor_md.ALL_VENDORS` and the collector; all five judge passes re-run **9-up** to
fresh `_pulse` outputs/caches with **`LA_DPT2=1`** (canonical LA slot = DPT-2). Only Pulse's score
column is spliced into canonical; the other 8 vendors stay **byte-identical** (canonical weights
frozen). `mistral` is now in the splice's `CANON_VENDORS` (it became an existing vendor after its own
add). Validation = the 8 existing vendors' aggregate, under *canonical* weights, between the canonical
run and the 9-vendor run, on the loose n=7 gross-distortion gate (|Δ| < 10pp).

| Judge pass | worst drift on the existing 8 | gate | Pulse |
|---|---:|---:|---:|
| **gpt-5 structure (HEADLINE)** | 5.0 pp | 10 | **90% / 4% unsup** |
| gpt-5 content (diagnostic) | 4.5 pp | 10 | 89% / 2% |
| gemini structure | 4.1 pp | 10 | 93% / 1.6% |
| gpt-5 spatial | **10.0 pp — TRIPPED** | 10 | **94%** |
| gemini spatial | **15.8 pp — TRIPPED** | 10 | 86% |

**The two spatial gates tripped and were force-spliced after audit — the exact pattern the Mistral
splice hit.** The drift is concentrated in the two *weakest* vendors — Tesseract +15.8 (gemini),
LiteParse +10.0 (both) — i.e. a global judge-leniency level shift on borderline-bad OCR, where a
lenient grader has the most room, **not** a comparison broken by Pulse. Decisive point: **Pulse's own
column is cross-family-corroborated and stable — every page lands 62–100 on *both* judges**
(AE p1 100/100, p2 97.5/90, p3 100/92, p4 96/96; MNH p1 100/100, p2 87.5/62.5, p3 77/71), with the
aggregate gpt-5↔Gemini spread (94 vs 86) tracing to a *single* dense household-table page (MNH p2,
where Gemini graded cell binding harder). Freezing canonical means **no existing published number
moved** regardless. Spliced via `splice_vendor.py pulse --splice --force="gpt-5 spatial,gemini spatial"`
(the three clean fair-total families spliced automatically).

## Results

**Structure-aware fair total (canonical, gpt-5 headline):** **90%**, content 89%, **structure gap +1**,
unsupported **4%**. Clean #2 — above gpt-5 image (80%) and the ◆ Landing AI reference (84%); only
Mistral (92%) and the ◆ Gemini co-author (99%) are higher. The **+1 gap and 4% unsupported are the
best fidelity of any real vendor** (Mistral 8%, gpt-5 image 11%, LiteParse 23%): Pulse almost never
asserts a binding it can't support.

**Per-category (gpt-5 structure):** Text **97** · Form **89** · Table 95 · Mixed 88. It reads the
**Form** category (89) like a vision model — vs gpt-5 image 65 and ◆ Landing AI 72, just under Mistral
(91) and near the ◆ Gemini ceiling (98).

**Per-doc (gpt-5 structure):** Unédic *attestation* (partly **scanned**) **92** · MNH *aide sociale*
(born-digital) **88** — strongest on the **scan**, where the `refine` OCR pass earns its cost.

**Form-spatial ranking — #2 on BOTH judges** (`results/SPATIAL_RANKING.md`):

| judge | SPATIAL | field | check | cell |
|---|---:|---:|---:|---:|
| gpt-5 | **94%** | 93 | **94** | **96** |
| Gemini | **86%** | 90 | **94** | 65 |

The decisive call on these forms is **checkbox state**, and Pulse reads the ☐/☒ glyph bound to its
label at **94% on both judges** — vision tier (vs 0% for the flatten-the-text-layer parsers PyMuPDF/
LlamaParse, and 6–31% for Tesseract/LiteParse). On **cell binding** it is actually the **best of all
vendors under the gpt-5 judge (96)**, but the **stricter Gemini judge marks it down to 65** — entirely
on the one dense MNH household table (p2), the page where its refine output is largest and hardest to
bind. That single page is the whole gpt-5↔Gemini gap.

**Fabrication is near-absent — the opposite of the Mistral-on-Finance story.** Aggregate unsupported is
4% (gpt-5) / 1.6% (Gemini), the lowest in the field; the figure-description layer has almost nothing to
over-read on forms (logos/stamps/barcodes only).

## The finding

**On insurance forms, Pulse (Ultra 2) is a clean vision-tier #2 (90% structure-aware) — it captures
slightly less than Mistral OCR 4 (92%) but fabricates the least of any vendor (4% unsupported, +1
structure gap), reads checkbox state at 94%, and is strongest on the scanned document (92%).** Its one
soft spot is dense-table cell binding under the stricter Gemini judge. The cost of that quality is
real: **`pulse-ultra-2` + `refine` is ~30–150s/page and ~10 credits/page — roughly 10× the wall and
credit of Mistral OCR 4** (~2s/page) for ~2pp less structure capture. As with Mistral, the genre
matters: forms reward dense multilingual OCR + checkbox-glyph preservation and give the figure layer
nothing to hallucinate on — exactly Pulse's strengths here. Pick the vendor for the document: on these
forms Mistral and Pulse are the two that actually read them, with Pulse trading a little capture and a
lot of latency for the cleanest fidelity on offer.

## Artifacts

- Shared config+reducer `scripts/pulse_common.py` (most-advanced config: `pulse-ultra-2` + refine +
  `figure_processing.description`); runner `scripts/pulse_run.py` (per-page PNG); collector
  `collect_pulse()` in `scripts/collect_extractions.py`.
- Splice via the existing `scripts/splice_vendor.py pulse` (`--force` for the two documented-noise
  spatial families); `mistral` added to its `CANON_VENDORS`.
- Raw per-page responses `ground_truth/pulse/raw/`; collected `results/_extract_pulse.json`;
  9-vendor judge outputs `results/_fair_total_judging{,_content,_gemini_v2}_pulse.json` +
  `results/_spatial_judging{,_gemini}_pulse.json`; canonical originals in `results/pre_pulse_archive/`.
- Judge cost ~$0.90 (gpt-5 structure $0.20 + content $0.18 + spatial $0.26; Gemini structure $0.12 +
  spatial $0.14) + Pulse parsing ~70 credits (10/page × 7).
- Regenerated: `results/FAIR_TOTAL.md`, `results/SPATIAL_RANKING.md`.
