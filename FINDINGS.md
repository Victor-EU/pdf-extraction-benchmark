# Findings — insurance-form extraction (current state)

Corpus: 7 pages, 2 French insurance forms. Ground truth: vision multi-source, reconciled
(see [`ground_truth/GT_RECONCILIATION.md`](ground_truth/GT_RECONCILIATION.md)).

## Executive summary

These are **forms**, so the deciding question is not "how many characters did the parser recover"
but "did it preserve the **spatial relationships** that give a form meaning" — each value bound to
its field label, each tick to its option, each cell to its row×column. Ranked on that, and nothing
else ([`results/SPATIAL_RANKING.md`](results/SPATIAL_RANKING.md), both judge families):

- **A vision model is required.** **Mistral OCR 4 is the clean #1 at 97% spatial fidelity** and gpt-5
  (image) follows at **84%**; the four text-layer / OCR tools (LiteParse, PyMuPDF, LlamaParse,
  Tesseract) sit at **30–39%**. The gap holds identically under a second (Gemini) judge.
- **The same tool that lost the finance benchmark wins this one — genre decides.** Mistral OCR 4
  (added 2026-06-23, [`MISTRAL_ADD.md`](MISTRAL_ADD.md)) was **5th of 10 and the fabrication outlier
  (19% unsupported)** on the sibling chart/finance corpus, and is the **clean #1 here (92%
  structure-aware, 8% unsupported, structure gap −1)**. Forms have no charts for its annotation layer
  to hallucinate on (its finance weakness disappears), and reward exactly its strengths — dense
  multilingual OCR, HTML tables that survive a binding check, and checkbox glyphs read at **100%**.
  This finance-vs-insurance flip is the single sharpest evidence in either repo that *the right
  extractor is a property of the document, not the tool in the abstract.*
- **Checkbox state is the decider — and the text layer barely carries it.** *Which box is ticked* —
  the single most consequential datum on a benefit/attestation form — splits the field by **how** a
  parser sees a tick. The parsers that read the native text layer and **flatten** it (PyMuPDF,
  LlamaParse) score **0%** under both judges: the `[X]` glyph is in the stream, but they detach it
  from its option. The tools that recover *anything* do so by two different routes, both crude:
  **Tesseract** OCRs the rasterized page and literally sees the mark (6% gpt-5 / 31% Gemini, noisy),
  and **LiteParse** keeps the text layer's `[X]` glyph *bound to its option* through its grid (22% /
  27%) — but both sit far below the **85–100%** of the vision models. A tick is a near-visual fact;
  only a model that reads the pixels recovers it reliably.
- **LiteParse (run-llama OSS, newly added) is the best text-layer tool *on forms* — and that ranking
  is genre-dependent, not a general verdict.** LiteParse detects no structure; it *reconstructs* it
  from 2-D position (PDFium text → grid projection). That bet pays off where a form's structure is
  spatially **sparse and local** — a printed label then its value, an isolated `[X]` — so here it
  holds field↔value adjacency and the tick glyphs, reaching **56%** structure-aware fair total (vs
  PyMuPDF 49 / Tesseract 44 / LlamaParse 31), #1 of the text-layer tools on spatial fidelity (39%).
  The *same* bet **backfired** on the sibling chart/finance corpus, where the grid merged a table's
  adjacent numeric columns into an unrecoverable run and LiteParse fell **below** a raw PyMuPDF dump.
  Even here it pays the corpus-high **23% unsupported** and the **largest structure gap (−20)** —
  garbled brackets (`[XI`/`[J`) asserting ticks that are not there. The transferable rule: a
  **layout-preserving heuristic suits forms; dense tables want a structure-detector or vision.**
- **Text-layer extraction stays disqualified for forms — even LiteParse.** Despite raw-content scores
  up to a perfect 100% (§1), the whole tier lands at 31–56% once bindings are required: the characters
  survive, the form does not. LiteParse merely loses *least*.
- **Landing AI is now benchmarked on its current DPT-2 model** — the legacy pre-DPT-2 endpoint was a
  config bug, fixed 2026-06-15. DPT-2 emits structured `[x]`/`[ ]` checkbox state and **corrected the
  one false tick the legacy model asserted**. As a `◆` ground-truth co-author it is not ranked, but it
  sits firmly in the vision tier (94% checkbox).

Up-front caveat: **n = 7 pages.** The vision-vs-text-layer gap is large and judge-robust; LiteParse
leads the text-layer tier but the order among the pure text-dumpers below it is a statistical tie,
and absolute scores are gpt-5-judge-specific. The
structure-aware fair total (§2), cross-family check (§2b), the spatial ranking (§2c) and per-vendor
detail (§3) follow.

## 1. Objective dimensions (free, deterministic) — and why they mislead here

Scored vs a text-layer ∪ image-OCR reference (`scripts/score_extraction.py`):

| Vendor | Content | Prec | Numbers | Order τ | Table-pres |
|---|---:|---:|---:|---:|---:|
| PyMuPDF | **100%** | 100% | **100%** | 90% | 100% |
| Gemini 3.5 Flash ◆ | 97% | 98% | 92% | 76% | 100% |
| Landing AI ◆ | 96% | 96% | 88% | 78% | 100% |
| LiteParse | 93% | 96% | 92% | – | 100% |
| Tesseract | 88% | 83% | 90% | 84% | 0% |

**Read this table with care.** The reference is derived from the text layer, and PyMuPDF
*is* a text-layer dump — so it scores a perfect 100% on content and numbers. That does **not**
mean PyMuPDF read the form. Its output is a flat run of labels followed, separately, by a run
of values:

```
Téléphone : Statut juridique : N° SIRET : Code APE/NAF :
33369592200414
8790A
```

The binding "SIRET = 33369592200414" is **destroyed**, and there is **no checkbox state at
all**. The objective dims are blind to exactly the two things these forms are about. Tesseract
emits 0 tables and mangles the dense grids. LiteParse scores nearly as high here (93–100%), but
the dims cannot see that it *keeps* more of the bindings than PyMuPDF does — that surfaces only in
the structure-aware metric (§2), where it pulls ahead (56% vs 49%). (Its reading-order τ is `–`:
it emits one whole-page markdown block, so there is no inter-block order to score.) `◆` =
ground-truth co-author (upper bound).

## 2. Structure-aware fair total (the canonical capture metric) — RUN

*This is the project's canonical document-capture metric (it already requires correct field/row/column
bindings and checkbox state). §2c then isolates the purely **spatial** relationships — the sharper,
form-decisive cut foregrounded in the executive summary.*

A blind gpt-5 judge graded each vendor's full extraction against the GT, crediting a value
only if its field/row/column binding is recoverable **and the checkbox state is correct**
(`scripts/score_fair_total_structure.py`; full table in [`results/FAIR_TOTAL.md`](results/FAIR_TOTAL.md)).

| Vendor | Fair total (structure-aware) | Content recall | Structure gap |
|---|---:|---:|---:|
| **Mistral OCR 4** | **92%** | 94% | −1 |
| gpt-5 (image) | **80%** | 79% | +1 |
| LiteParse | 56% | 76% | **−20** |
| PyMuPDF | 49% | 71% | **−23** |
| Tesseract | 44% | 59% | **−15** |
| LlamaParse | 31% | 39% | −7 |
| Gemini 3.5 Flash ◆ | 99% | 98% | 0 |
| Landing AI (DPT-2) ◆ | 84% | 88% | −4 |

`◆` = ground-truth co-author (upper bound, not ranked). Landing AI is its current **DPT-2** model
(`v1/ade/parse`; the benchmark previously used the legacy pre-DPT-2 endpoint — config fixed
2026-06-15). On DPT-2 it extracts the form tables/attestation blocks the legacy model dumped as
`figure`; its fair-total moved 87→84, but that is **within the n=7 judge-noise floor** (untouched
vendors drifted up to ±6pp on the same re-judge), so read it as "unchanged, now on the correct
model." It stays ◆ because the *legacy* LA lightly co-authored the GT. **Mistral OCR 4 is the clean
winner at 92%** (above even the ◆ Landing AI reference, 84%), with **gpt-5 second at 80%**;
**LiteParse leads the local/text-layer tools (56%)** but still sheds 20 points to the binding check;
the pure text-dumpers collapse — PyMuPDF loses **23 points** (vs −16 in the original chart corpus),
Tesseract 15. The per-category breakdown is the proof the metric measures *structure*, not
strictness:

| | Text (prose) | Form | Table |
|---|---:|---:|---:|
| PyMuPDF | 99% | **29%** | **35%** |
| LiteParse | 95% | 51% | 55% |
| gpt-5 (image) | 97% | 65% | 100% |
| **Mistral OCR 4** | 90% | **91%** | 98% |
| Gemini 3.5 Flash ◆ | 99% | 98% | 100% |

PyMuPDF reads the cover-letter prose perfectly (99%) and **craters exactly where the form
structure lives** (Form 29%, Table 35%) — because its output is a flat run of labels and a
separate run of values, with no field bindings and no checkbox state. LiteParse, on the same text
layer, nearly *doubles* PyMuPDF on Form (51%) and Table (55%) — its grid projection holds the
label↔value adjacency PyMuPDF flattens — yet still falls well short of the form-aware LLMs.
**Mistral OCR 4 dominates the Form category (91%)** — the hardest, most form-specific pages — far
above gpt-5 (65%) and the ◆ Landing AI reference (72%), near the ◆ Gemini ceiling (98%): its HTML
tables and preserved checkbox glyphs hold the bindings the text-layer tools shed.

## 2b. Cross-family judge — is the headline judge-dependent?

The headline above is from a **gpt-5** judge, and gpt-5 is also a graded vendor — so the obvious
objection is judge self-preference. We re-ran the **byte-identical** rubric with a **Gemini 3.5
Flash** judge (`scripts/score_fair_total_structure_gemini.py`, only the judge model differs):

| Vendor | gpt-5 judge | Gemini judge | Clean rank (both) |
|---|---:|---:|---|
| **Mistral OCR 4** | **92%** | **98%** | **#1 under both** |
| gpt-5 (image) | 80% | 94% | **#2 under both** |
| LiteParse | 56% | 73% | #3 / #4 |
| PyMuPDF | 49% | 67% | #4 / #5 |
| Tesseract | 44% | 78% | #5 / #3 |
| LlamaParse | 31% | 43% | #6 under both |
| Gemini 3.5 Flash ◆ | 99% | 100% | — |
| Landing AI (DPT-2) ◆ | 84% | 92% | — |

What survives the judge swap (the load-bearing claims):
- **No self-preference.** The #1 clean vendor under *both* judges is **Mistral OCR 4, not the
  gpt-5-family judge's own gpt-5** — and the gpt-5 judge is in fact **harsher** on gpt-5 (80) than
  the Gemini judge is (94). A self-preferring gpt-5 judge would do the opposite; the headline is if
  anything conservative.
- **The structure collapse replicates.** PyMuPDF reads prose (Text 99% / 100%) but cliffs on forms
  (Form 29% / 54%) under both judges, and gpt-5 holds on forms (65% / 90%) under both. The
  text-dumper-loses-structure thesis is not an artifact of one judge.
- **LiteParse leads the text-layer tools under the headline judge** (#3 clean behind Mistral OCR 4
  and gpt-5; structure 56 vs PyMuPDF 49 / Tesseract 44) — its grid-projection advantage over the pure
  text-dumpers holds on the gpt-5 read. Under the more *lenient* Gemini judge it slips to #4 as
  Tesseract's pixel-OCR is scored generously (78 vs LiteParse 73), so "best local tool on forms" is a
  headline-judge claim, not a both-judge one; the durable part is that all of them sit far below the
  vision tier.
- **LlamaParse is last under both.**

What does *not* survive (disclosed, not hidden):
- **Absolute scores are judge-dependent.** Gemini grades uniformly more leniently (+6 to +34 pts
  across clean vendors). Read the single number "80%" as *gpt-5-judge-specific*; the cross-judge
  spread is the real uncertainty band.
- **The text-layer floor order is within judge noise** — PyMuPDF, Tesseract and LiteParse all swap
  places between judges (e.g. the lenient Gemini judge lifts Tesseract's pixel-OCR above LiteParse,
  78 vs 73, reversing the gpt-5 order). We do **not** claim a firm ordering inside this tier; all
  three are "recovers characters, loses form structure," and all sit far below the vision tier under
  both judges.

**Which judge to trust (hand-audit verdict).** The leniency is not a neutral level shift — a
page-by-page hand audit against the pixels shows the **Gemini judge specifically under-penalises the
two error types this benchmark cares about most**, while the gpt-5 judge catches them:
- *Contradictions.* On the **legacy** Landing AI's **false `portage salarial` tick** (AE p2), the
  gpt-5 judge flagged 35% unsupported; the Gemini judge flagged 5% — it essentially **missed the wrong
  binding**. (DPT-2 Landing AI later corrected this tick to blank, so the contradiction is gone from
  the current data — but the judge-sensitivity point stands: the gpt-5 judge is the one that catches
  wrong bindings.)
- *Garble.* On Tesseract's heavily mangled OCR (AE p1: NIR read as `[11814 2i4 4lol1`, "Pôle"→"P6le"),
  the gpt-5 judge gave 30/40; the Gemini judge gave 85/10 — **crediting unreadable output as recall**.
Both judges agree on the *ranking*, but the gpt-5 judge's *absolute* numbers are the defensible ones,
so it stays the headline. The Gemini run's value is confirming the order, not the magnitudes.

## 2c. Spatial-relationship ranking — what matters most on a form

The fair total blends prose recall with structure. But on a form, what matters *most* is the
**spatial relationship**: a value's meaning comes entirely from its 2-D position. So we ranked every
vendor on a metric that scores ONLY the spatial relationships, split into the three that exist on
these forms — judged blind by both families (`scripts/score_spatial.py`, full table in
[`results/SPATIAL_RANKING.md`](results/SPATIAL_RANKING.md)):

| Vendor | **SPATIAL** | field→value | **checkbox** | table cell |
|---|---:|---:|---:|---:|
| **Mistral OCR 4** | **97%** | 96% | **100%** | 95% |
| gpt-5 (image) | **84%** | 89% | **85%** | 75% |
| LiteParse | 39% | 67% | **22%** | 15% |
| PyMuPDF | 32% | 66% | **0%** | 17% |
| LlamaParse | 31% | 62% | **0%** | 35% |
| Tesseract | 30% | 58% | **6%** | 10% |
| Gemini 3.5 Flash ◆ | 99% | 98% | 100% | 98% |
| Landing AI (DPT-2) ◆ | 92% | 93% | 94% | 88% |

*(gpt-5 judge; the Gemini judge gives the same vision-vs-text-layer split — Mistral OCR 4 97%, gpt-5
85%, the text-layer tools 36–49% — with the within-text-layer-tier order flipping, n=7 noise. Under
Gemini, LiteParse checkbox is 27%. Mistral's spatial score is corroborated across both judges, 97% vs
97%; on this family the Gemini re-judge ran globally more lenient on the weakest OCR tools, so per
[`MISTRAL_ADD.md`](MISTRAL_ADD.md) its Gemini-spatial column was spliced with an explicit audited
override while canonical stayed frozen.)*

**The checkbox column is the whole story — and it sorts the tools by *how each one sees a tick*.**
Checkbox/radio state — *which box is ticked*, the single most consequential datum on a
benefit/attestation form — separates into three mechanisms:

1. **Flatten the text layer → 0%.** PyMuPDF and LlamaParse read the native text layer and dump it in
   a flat order. The `[X]` glyph is *present* in the stream, but detached from its option, so it
   conveys nothing — **0% under both judges.**
2. **OCR the pixels → noisy partial.** Tesseract rasterizes the page and OCRs it, so like a crude
   vision model it literally sees the mark (**6% gpt-5 / 31% Gemini** — the lenient Gemini judge
   crediting more). It reads ticks it can *see*, independent of any text layer.
3. **Preserve the glyph's position → noisy partial.** LiteParse stays in the text layer but its grid
   projection keeps the `[X]` glyph *bound to its option* (**22% gpt-5 / 27% Gemini**) — the same
   characters PyMuPDF flattens, kept in place. (Notably, under the Gemini judge Tesseract's pixel-OCR
   (31) edges LiteParse's glyph-preservation (27): two different crude routes to the same low tier.)
4. **Read the pixels with understanding → reliable.** Only the vision models clear the bar — **Mistral
   OCR 4 100%** (it preserves the ☐/☒ glyph bound to its option and reads the tick state outright) and
   **gpt-5 85%**, with the ◆ co-authors Gemini/Landing AI **94–100%**. An OCR-class model with a
   form-aware reduction is squarely in this tier; the route, not the "OCR" label, is what matters.

So the four text-layer/OCR tools recover field→value pairs partially (58–67%, from label/value
proximity in the stream) but collapse on the genuinely 2-D relationships — checkboxes (0–27%) and
table cells (10–35%). The vision-vs-rest gap (Mistral 97 / gpt-5 84 vs 30–39) dwarfs the n=7 noise and is identical
across judges; within the lower tier LiteParse leads on the composite, but on checkboxes specifically
it and Tesseract are a noisy near-tie and the flatteners are at zero. **Headline for forms: if
checkbox/field-binding fidelity matters, a vision model is not optional — every non-vision route to a
tick here is, at best, partial and unreliable.**

## 3. Vendor-specific findings

- **gpt-5 (image)** is the **#2 clean vendor (80%, behind Mistral OCR 4)** and has effectively no
  structure gap (+1) — it emits faithful `field`/`choice` structure and asserts no **false** checkbox
  state. But strong is not "flawless": on AE p1 a hand audit against the page
  pixels found it **misread the NIR** (`…0 1 1 8 1` for the true `…0 1 8`), **the date of birth**
  (`05/05/1984` for `05/06/1984`), **missed the `statut cadre = non` tick**, and **hallucinated the
  footer**; on AE p2 it **omitted the rupture motive (code 31)** and two `non` ticks. Across the
  corpus it captures 11 of the GT's 15 ticks — all 11 correct, 4 omitted. Its failure mode is
  **under-capture and the occasional wrong value, not wrong bindings** — which is exactly why the
  gpt-5 judge's harsh 70/40 on AE p1 is *justified*, not self-deprecation. (Hand audit:
  `archive/` page crops; the NIR/DOB errors are the canonical "confident silent error on a PII
  field" this benchmark warns about.)
- **Gemini 3.5 Flash reads these forms remarkably well** (and co-authored the GT): 22/22 field
  values on the densest page grounded in the text layer, and **15/15 checked boxes confirmed
  correct** at high res — including the single ticked box on the MNH demande grid that looks
  blank at low resolution.
- **Landing AI (DPT-2)** — re-benchmarked on its current `v1/ade/parse` `dpt-2-latest` model (the
  benchmark previously hit the legacy pre-DPT-2 endpoint; config fixed 2026-06-15). DPT-2 is a real
  upgrade *on forms*: where the **legacy** model summarised dense form regions as `figure`, DPT-2
  emits actual form tables, `attestation` blocks, and **structured `[x]`/`[ ]` checkbox state** — so
  its spatial scores are top-tier (field 93%, checkbox 94%, cell 88%; §2c). Crucially it **corrected
  the one contradiction the audit had flagged**: the legacy false tick `[x] salarié en portage
  salarial` (AE p2, blank in the form) is now correctly `[ ]`. It stays `◆` (the *legacy* LA lightly
  co-authored the GT) so it is not ranked; its fair-total moved 87→84, within the n=7 judge-noise
  floor. Net: DPT-2 turned Landing AI from a figure-dumper-with-a-false-tick into a genuine,
  precise form extractor — and it remains the one option here that also emits exact bounding boxes.
- **LlamaParse fails on the MNH mutuelle form**: `NO_CONTENT_HERE` for 2 of its 3 pages and a
  garbled `l l l l …` run for the third (the watermarked/boxed form defeats its parser),
  dragging it to 31% overall and 0% on the Text page. It fared better on the Unédic doc.
- **LiteParse (run-llama OSS — LlamaParse's core minus the VLM)** is the strongest text-layer tool
  here, the *reverse* of its sub-PyMuPDF placing on the chart/finance corpus. On these forms its
  PDFium-native text + anchor "grid projection" keeps each filled value beside its label
  (`Prénom : Fadhel`, `N° SIRET : 33369592200414`) and — uniquely among the *text-layer* (non-OCR)
  tools — preserves the tick glyph (`[X] Ressortissant français`) bound to its option, so it scores
  56% structure-aware / 39% spatial / 22% checkbox where PyMuPDF and LlamaParse (which flatten the
  same glyph away) read 0 ticks. The price is its garbled
  brackets (`[XI`, `[J`, `[I`, `[\_]`) and merged checkbox runs, which give it the **corpus-high
  23% unsupported** (wrong/ambiguous tick assertions) and the **largest structure gap (−20)**.
  Free, local, vision-blind (figures stripped) — a credible free baseline for *forms*, but it does
  not close the vision gap on the decisive checkbox call.
- **Mistral OCR 4 (advanced config — `mistral-ocr-4-0` + HTML tables + per-image annotation)** is the
  clean #1 (92% structure-aware, 97% spatial), the new top of the field. Its reduction preserves the
  checkbox glyphs (☐/☒) bound to their labels and inlines tables as HTML with rowspan/colspan, so it
  reads tick state at **100%** and lands a near-zero **−1 structure gap**. It dominates the Form
  category (91%) and is strong on both the born-digital MNH form (93.8) and the scanned Unédic
  attestation (91.5). Fabrication — the trait that made it the *worst* of 10 on the chart/finance
  corpus (19% unsupported) — is here only **8%** and localized to two low-signal pages (the dense
  rupture/indemnity page AE p4 at 25%, the MNH cover letter p1 at 20%, where the annotation layer
  over-asserts). The contrast is the benchmark's clearest single proof that genre, not the tool,
  picks the winner; full method + the gemini-spatial splice audit in [`MISTRAL_ADD.md`](MISTRAL_ADD.md).
  Still, even the new #1 fabricates on low-information pages — so the "winner fails silently" warning
  (above, for gpt-5's NIR/DOB misreads) generalizes: surface confidence scores and gate derived claims
  regardless of which vendor leads.
- **Checkbox state is the separator** here, as chart-data fidelity was in the original corpus:
  near-invisible to the text layer, it cleanly divides form-aware vision tools from the rest — with
  only two partial, unreliable non-vision routes to a tick (LiteParse's glyph-preserving grid 22–27%,
  Tesseract's pixel OCR 6–31%), both far below the vision tier.

## Cost

Total API spend for the full benchmark on this 7-page corpus: **~$1.03** (Gemini GT $0.31 +
gpt-5 extraction $0.31 + gpt-5 structure judge $0.17 + content judge $0.15 + Gemini cross-family
judge $0.09; Landing AI & LlamaParse on free tiers). The **DPT-2 Landing AI re-benchmark**
(2026-06-15) added ~21 Landing AI credits + **~$0.58** in re-judging (structure gpt-5 $0.16 +
structure Gemini $0.09 + content $0.15 + spatial gpt-5 $0.18 + spatial Gemini $0.10). The
**LiteParse add** (2026-06-23, run-llama OSS, local/free to run) added **~$0.81** in re-judging
all 7 vendors 7-up (structure gpt-5 $0.19 + content $0.16 + structure Gemini $0.10 + spatial gpt-5
$0.24 + spatial Gemini $0.12); its column was spliced into canonical with the existing six frozen.
The **Mistral OCR 4 add** (2026-06-23, advanced config) added **~$0.87** — ~$0.04 parsing ($5/1k-page
Document-AI tier) + ~$0.83 re-judging all 8 vendors 8-up (structure gpt-5 $0.18 + content $0.17 +
structure Gemini $0.11 + spatial gpt-5 $0.24 + spatial Gemini $0.13); its column was spliced into
canonical with the existing seven frozen.

_Numbers are from the dated vendor model versions on this 7-page private corpus._
