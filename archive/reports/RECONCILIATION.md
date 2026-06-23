# Reconciliation — Why two PDF-extraction experiments rank Landing AI differently

> **Numbers here are content-recall-era (the headline went structure-aware 2026-06-14, see
> [`STRUCTURE_AWARE_SCORING.md`](STRUCTURE_AWARE_SCORING.md)).** The cross-experiment reconciliation
> is unaffected — both experiments used content/atomic-fact recall, so this is the right basis for
> comparing them. Under the new structure-aware headline the fair-total values shift (e.g. PyMuPDF
> 84→68, Landing AI 87→81); the *relationship* between the two experiments is unchanged.

**Date:** 2026-06-13
**Author:** independent cross-read of two experiments by their respective owner
**Subjects:**
- `PDF parsing test/` — this repo. Density-weighted document-level **information capture**, 8 vendor configs, 599 pages, 3 documents. Headline: Gemini 3.5 Flash 92%, Landing AI **87%** (4th among clean vendors).
- `pdf-extraction-audit/` — sibling repo at `/Users/vz/pdf-extraction-audit`. Atomic-**fact recall**, 4 vendors, 576 pages, 3 documents. Headline reads, on first glance, as **Landing AI co-leading / "best on the long structured IAR."**

> **Numbers refreshed 2026-06-13** to this repo's corrected canonical (v2 text-layer GT + the no-truncation `VEND_CAP` re-judge, see `AUDIT_VEND_CAP.md`). Both corrections *raised Landing AI* — its blend moved 84.5→**87.4%** and its shared-IAR score 93.7→**94.3%** — so the shared-document agreement is now **94.3 (here) vs 93.6 (audit) ≈ 0.7pp** rather than the 0.1pp of the earlier draft. The sibling-repo (`pdf-extraction-audit`) numbers are unchanged. **The reconciliation's argument is unaffected; only the magnitudes shifted.**

> **One-line verdict:** The two experiments are **consistent, not contradictory.** On the one document they physically share — a byte-identical 310-page annual report — they score Landing AI at **93.6%** and **94.3%** respectively, a 0.7pp agreement. The apparent headline gap (LA "SOTA" vs LA "4th at 87%") is produced entirely by three controllable framing differences — **document mix, vendor pool, and the audit's acknowledged ground-truth self-bias** — not by an error in either experiment.

> **⚠ LlamaParse tier correction (2026-06-13) — supersedes the LlamaParse analysis below.** This reconciliation originally explained the LlamaParse gap (this repo **74.7%** vs audit **87.8%** on the shared IAR) as a *metric* divergence ("this repo also scores the figures LlamaParse omits"). **That explanation was wrong — the gap was a *tier confound*.** This repo had run LlamaParse in its middle **`accurate`** tier; the audit used the **`agentic`** tier. Re-running this repo at **`agentic`** (`AUDIT_LLAMAPARSE_MODE.md`) raises LlamaParse to **95.5% on the shared IAR** (90% across all 599 pages) — now **above** the audit's 87.8%, not 13 points below it, and LlamaParse-agentic demonstrably **does read figures** (charts 83, diagrams 83 element-level). The two experiments now *agree* LlamaParse is a strong, figure-capable parser; the residual 95.5-vs-87.8 is the ordinary LLM-judge-vs-fact-matcher metric difference (this repo's judge is the more generous on born-digital text). The LlamaParse-specific paragraphs in §1.5, §5, §7 below are kept for the record but read them through this correction.

---

## 1. TL;DR for the impatient

1. **They share exactly one document** (eDreams IAR FY25, md5 `b4ec6744…`, 310pp) and on it they agree on Landing AI to within **~0.7 percentage points** (93.6 audit / 94.3 here). The experiments do not disagree about Landing AI's quality.
2. **Landing AI is genuinely strong on born-digital annual reports (~94%) and genuinely weaker on chart/diagram-heavy decks (~80%).** My corpus is ⅔ decks; the audit's corpus is ⅔ annual reports. Same per-document scores, different averaging weights → different headlines.
3. **The audit never tested Gemini.** On the shared document Gemini Flash (96.2) edges Landing AI (94.3); the audit's "LA is #1 on the IAR" only holds because the model that actually beats it wasn't in the race.
4. **The audit does not actually conclude "LA is SOTA."** Its own text says *"no single vendor dominates,"* and on its de-biased ("strong-only") metric **Landing AI wins zero of three documents.** The "SOTA" impression comes from the self-biased column.
5. **Neither experiment has a material error on Landing AI.** Each carries a known, bounded bias pointing in a *different* direction, and each mitigated it. The one large apparent LlamaParse gap turned out to be a **tier confound** (this repo ran `accurate`, the audit `agentic`) — fixed by re-running this repo at `agentic`, after which the two **agree** LlamaParse is strong (see the ⚠ banner above and `AUDIT_LLAMAPARSE_MODE.md`).

---

## 2. The two experiments at a glance

| | `PDF parsing test/` (this repo) | `pdf-extraction-audit/` |
|---|---|---|
| **Question** | What fraction of a document's *real information* does each vendor convey? | Does each GT *fact* appear somewhere in the vendor's output? |
| **Primitive** | Page-level holistic info capture, density-weighted | Atomic fact: text span / numeric value↔label / diagram node |
| **Score** | Fair total = Σ(info_recall × page_weight) ÷ Σ(page_weight) | Recall = matched_facts ÷ GT_facts (**no precision**) |
| **Scoring instrument** | LLM judge (gpt-5), blind, vendors shuffled A–H, per page | Deterministic string/token matcher (2000-char proximity window) |
| **Paraphrase** | Credited (correct-but-different words score full) | Credited implicitly (substring/token match is loose) |
| **Hallucination** | Measured as a separate `unsupported` fidelity column (not subtracted) | Not measured (recall-only by design) |
| **Ground truth** | gpt-5 vision 599-page transcription (v2, text-layer-corrected); Claude-vision audited | GPT-5.5 + Claude-Sonnet-4.6 vision consensus, **Landing AI as tie-breaker** |
| **Vendors** | gpt-5 image, gpt-5 file, **Gemini 3.5 Flash**, **Gemini 3.1 Flash-Lite**, Landing AI, LlamaParse, **PyMuPDF**, **Tesseract** | GPT-5.5, **Claude Opus 4.7**, Landing AI, LlamaParse |
| **Corpus** | IAR 310pp · Alpha 156pp **deck** · SOTER 133pp **deck** (599) | eDreams IAR 310pp · lastminute 133pp **annual report** · FIREBIRD 133pp **deck** (576) |
| **Reported headline** | Gemini Flash 92% > Flash-Lite 90% ≈ **LlamaParse 90%** (agentic) > **LA 87%** > PyMuPDF 84% > Tesseract 64% | "No single vendor dominates"; full-GT shows LA highest-looking on 2/3 docs; strong-only shows GPT/Claude on top |

**Vendors in common:** Landing AI and LlamaParse (exact same product). The GPT family appears in both but at different model versions and access modes, so it is only loosely comparable. Gemini, PyMuPDF, Tesseract are unique to this repo; Claude-as-a-vendor is unique to the audit.

**Documents in common:** exactly one — the eDreams IAR (proof below).

---

## 3. The control point: one byte-identical document

Both experiments ingested the same physical file:

```
md5  b4ec6744fc4b929d339dc41455b7e1ca   pdf-extraction-audit/corpus/edreams_iar_fy25.pdf
md5  b4ec6744fc4b929d339dc41455b7e1ca   PDF parsing test/Data/IAR_FY25_EN.pdf
310 pages in both.
```

This is the cleanest possible cross-experiment anchor: identical bytes, identical page count, two independent ground truths, two independent metrics, two independent scoring instruments built by partially different model families. On that document, the Landing AI numbers are:

| Landing AI on the eDreams IAR (310pp) | Score |
|---|---|
| `pdf-extraction-audit` — combined recall (full GT) | **93.6%** |
| `PDF parsing test` — fair-total capture | **94.3%** |

**~0.7pp apart.** A deterministic fact-recall matcher and a holistic LLM judge, on different ground truths, converge to within a point for Landing AI on this document. Whatever is driving the headline difference, **it is not a disagreement about how good Landing AI is.**

For completeness, the full vendor field on this one shared document:

| Vendor | `PDF parsing test` (capture) | `pdf-extraction-audit` (full-GT recall) | `pdf-extraction-audit` (strong-only) |
|---|---:|---:|---:|
| gpt-5 (image) | 96.3% | 91.6% (GPT-5.5) | 88.8% |
| Gemini 3.5 Flash | 96.2% | *not tested* | — |
| Gemini 3.1 Flash-Lite | 95.1% | *not tested* | — |
| gpt-5 (file) | 95.0% | — | — |
| **Landing AI** | **94.3%** | **93.6%** | 89.5% |
| Claude Opus 4.7 | *not tested* | 92.6% | **89.7%** |
| PyMuPDF | 89.6% | *not tested* | — |
| LlamaParse | 74.7% | 87.8% | 87.2% |
| Tesseract | 71.0% | *not tested* | — |

Two things jump out, and they are the whole story (Sections 4–5):
- Landing AI agrees across experiments (93.6 / 94.3). **Gemini, which this repo tested and the audit did not, sits above it (96.2).**
- LlamaParse is the one vendor where the two metrics genuinely disagree (74.7 here vs 87.8 there).

---

## 4. Why the *headlines* differ — three factors, in order of magnitude

### Factor 1 — Document mix (the dominant cause)

Landing AI's quality is strongly content-dependent. Its per-document fair-total in this repo:

| Document | Type | Landing AI capture |
|---|---|---:|
| IAR_FY25 | born-digital **annual report** (structured text + financial tables) | **94.3%** |
| Alpha | French consulting **deck** (dense charts/diagrams) | 82.2% |
| SOTER | investor **deck** (label-free charts, photos, logos) | 78.6% |

Landing AI swings **~14pp** between the annual report and the decks. That single fact explains the headline gap, because the two corpora are weighted oppositely:

| Corpus | Annual reports | Decks | LA-favorability |
|---|---|---|---|
| `pdf-extraction-audit` | lastminute (133) + eDreams IAR (310) | FIREBIRD (133) | **LA-favorable** (⅔ reports) |
| `PDF parsing test` | IAR (310) | Alpha (156) + SOTER (133) | **LA-hostile** (⅔ decks) |

My headline Landing AI = **87.4%** is the page-weighted blend of one 94.3% document and two ~80% documents. The audit's headline is a blend of mostly annual reports. **Identical per-document behavior, different mixing weights.** If I restricted my corpus to annual-report-type pages, Landing AI would rise toward the mid-90s and the "discrepancy" would largely vanish.

This is not a defect in either experiment — it is the experiments correctly reporting that **vendor ranking is content-dependent**, a point the audit itself makes ("per-doc winner is content-dependent").

### Factor 2 — The vendor pool decides who is "#1"

The audit tested four vendors; Gemini was not among them. On the shared IAR the ranking is:

```
gpt-5 96.3  ·  Gemini Flash 96.2  ·  Flash-Lite 95.1  ·  gpt-5 file 95.0  ·  Landing AI 94.3  ·  …
```

Landing AI is **fifth**, but only because three configs the audit didn't run (two Gemini, gpt-5-file) sit above it. Remove Gemini and gpt-5-file and Landing AI is back near the top alongside gpt-5 — which is *exactly* what the audit reports ("Best on long structured IAR"). The audit's "LA leads the IAR" and this repo's "Gemini leads the IAR" describe **the same reality** through different vendor pools. Neither is wrong; they're answering "who's #1 *among the vendors I tested*."

### Factor 3 — The audit's headline impression is partly a ground-truth self-bias

The premise that the audit "places Landing AI as SOTA" overstates what the audit concludes. Its FINDINGS.md says verbatim:

> *"no single vendor dominates"* … *"No clear cross-doc winner on recall."*

The "SOTA" impression comes from the **full-GT** recall column, where Landing AI looks highest on 2 of 3 documents. But the audit's own ground truth uses **Landing AI as the tie-breaker** that decides whether a disputed fact (emitted by only one of the two vision proposers) enters the answer key. That hands Landing AI automatic credit on the "LA-broken" stratum, which the audit measures as a self-bias of:

| Document | LA full-GT minus strong-only (self-bias) |
|---|---:|
| lastminute | **+5.4pp** |
| eDreams IAR | **+4.1pp** |
| FIREBIRD | **+2.4pp** |

The audit flags this as *"the most important caveat to publish"* and reports a de-biased **strong-only** column. On strong-only GT, **Landing AI wins zero of three documents**: Claude takes both annual reports (lastminute 87.4, IAR 89.7), GPT takes the deck (FIREBIRD 94.8). So the audit's *honest* metric already agrees with this repo's finding that **LLM vision edges Landing AI**; the disagreement only exists against the self-biased column.

---

## 5. Where the two metrics *genuinely* diverge — and why both are right

The large apparent LlamaParse gap looked like a metric divergence but was actually a **tier confound** — the single most important correction in this document:

| Vendor, on the shared IAR | `PDF parsing test` | `pdf-extraction-audit` | Δ |
|---|---:|---:|---:|
| Landing AI | 94.3% | 93.6% | **+0.7** |
| LlamaParse — *as originally run* (this repo `accurate` tier vs audit `agentic`) | 74.7% | 87.8% | **−13.1** |
| **LlamaParse — both at `agentic` tier** | **95.5%** | **87.8%** | **+7.7** |

- **The −13.1 was not a metric difference; it was a tier difference.** This repo had run LlamaParse in its middle **`accurate`** tier, which silently dropped whole born-digital pages (e.g. the IAR auditor's-report section scored ~0). The audit used the most-capable **`agentic`** tier. Same product, different mode.
- **Re-run at `agentic`, this repo scores LlamaParse 95.5% on the shared IAR — *above* the audit's 87.8%, not below it.** The sign of the gap flips. LlamaParse-agentic captures figures too (charts 83, diagrams 83 element-level), so the old "it emits no figure descriptions" explanation is simply false for the capable tier.
- The residual 95.5-vs-87.8 is the *ordinary* instrument difference: a generous paraphrase-crediting LLM judge vs a deterministic fact-matcher, on a born-digital text-heavy document where the LLM judge runs slightly hot. It is the same ~1–8pp instrument spread seen elsewhere, not a structural disagreement.

**Lesson for cross-experiment reconciliation: confirm both sides used the same vendor *tier/mode* before attributing a gap to the metric.** Here, two-thirds of a 13-point "metric divergence" was a configuration mismatch hiding in plain sight.

A second, orthogonal axis the audit deliberately ignores: **fidelity.** This repo's judge measured Landing AI's `unsupported` (claims it asserts that the page does not support) at **11.6% on the IAR** and **17.0% across all three documents — the highest of any real vendor.** The audit is recall-only and by design does not penalize this padding. So even where the two agree on recall/capture, this repo carries a fidelity signal the audit cannot see — relevant if you care about a parser inventing plausible-but-wrong figure prose, not just covering the facts.

---

## 6. Error audit — is either experiment wrong?

Both carry a known bias. Crucially, the biases point in **opposite directions** and each was mitigated, so they do not stack into a shared blind spot.

| | `pdf-extraction-audit` | `PDF parsing test` |
|---|---|---|
| **Structural bias** | GT uses **Landing AI as tie-breaker** → inflates LA | gpt-5 **judge scores against a gpt-5-built GT** → twin-family risk |
| **Direction** | Favors **Landing AI** (+2.4 to +5.4pp on full GT) | Could favor **gpt-5** |
| **Magnitude (measured)** | +2.4 to +5.4pp, isolated to the "LA-broken" stratum | gpt-5 beats Gemini by only **~1pp** (in fact Gemini Flash edges it) ; twin advantage is mild |
| **Mitigation** | Reports **strong-only** GT with LA's tie-break facts removed | **Independent Claude-vision audit** of the GT (found + corrected real figure defects, §9 of FINAL_REPORT); financial tables arithmetically self-consistent across pages (model-independent proof); a per-vendor judge-input truncation bug that deflated Landing AI was found and fixed (`AUDIT_VEND_CAP.md`) |
| **Residual blind spot** | Ignores hallucination/padding (recall-only) → can't see LA's 17% unsupported | Single holistic judge per page (subjective vs the audit's deterministic matcher) |
| **Net** | LA's full-GT lead is partly artifactual; honest metric agrees LLM vision wins | Ranking robust; gpt-5's GT-twin edge too small to move the order |

**Conclusion: no material error in either.** The audit's only overstatement is presentational — the full-GT column reads as "LA SOTA" to a quick reader, but the document's own prose and its strong-only column do not claim that. This repo's only residual risk (twin-family GT) was the subject of a dedicated cross-family audit that cleared it.

---

## 7. The unified picture

Put both experiments on equal footing — same document, same vendor pool, fidelity counted — and they tell **one** story:

1. **On structured, born-digital financial reports**, the strong vendors cluster within a few points (mid 90s) and **Landing AI is fully competitive** there (~94%, cross-validated by both experiments on the identical IAR file). This is the audit's home turf and its core finding survives.
2. **On chart/diagram/photo-heavy decks**, the multimodal LLMs (Gemini, gpt-5) pull clearly ahead and **Landing AI falls back to ~80%** because it under-recovers figure data and pads with some unsupported prose. This is this repo's core finding and it survives.
3. **LlamaParse, in its `agentic` tier, is a top-cluster figure-capable parser** — both experiments now agree (audit 87.8% / this repo 95.5% on the shared IAR; 90% across this repo's 599 pages). Its earlier last-place 71% here was a *tier* artifact (the `accurate` tier dropping pages), not a capability ceiling. The cautionary tale is about **choosing the vendor's most capable mode**, not about LlamaParse.
4. **"Who is #1" is not a stable global fact** — it depends on the document type and which vendors you put in the race. The honest cross-experiment statement is: *LLM vision ≈ Landing AI ≈ LlamaParse-agentic on born-digital annual reports; LLM vision > Landing AI on chart-heavy decks; the pure text-layer parsers (PyMuPDF/Tesseract) trail wherever figures matter.*

There is no contradiction to resolve. There is a single content-dependent ranking, sampled by two experiments on partially different documents with partially different vendor pools and two different but compatible metrics.

---

## 8. What each experiment is authoritative for

- **Use `pdf-extraction-audit` when** the question is *verbatim fact/number recall on born-digital financial statements* (the financial-analyst-agent ingest decision). It is the better-instrumented experiment for that narrow, high-stakes task: deterministic matcher, fact-level stratification, explicit strong-vs-full GT. Read the **strong-only** column, not full-GT.
- **Use `PDF parsing test` when** the question is *how much of a whole multi-modal document (charts, diagrams, photos, decks) is actually conveyed*, and when you need vendors the audit didn't cover (Gemini, PyMuPDF, Tesseract) or a fidelity/hallucination signal. It is the broader-corpus, broader-vendor, capture-oriented experiment.
- **Do not** compare a headline number from one against a headline number from the other without first matching document type and vendor pool. The only directly comparable cell is the shared IAR (93.6 ≈ 94.3).

---

## 9. Caveats of this reconciliation itself

- **n = 1 shared document.** The ~0.7pp Landing-AI agreement is a single, very clean data point, not a distribution. It is strong evidence the experiments are measuring compatible things on structured content; it is not proof they would agree on every document. The Alpha/SOTER ↔ lastminute/FIREBIRD decks are *not* shared, so the deck-side comparison is type-matched, not document-matched.
- **GPT family is only loosely comparable** across experiments (different model version, different access mode — per-page vision vs `input_file`), so I lean on Landing AI and LlamaParse (identical products) as the cross-experiment bridge.
- **Two metrics, not one.** Even at 93.6 ≈ 94.3 on the IAR, a deterministic fact matcher and an LLM judge are different instruments; their agreement here is reassuring but partly fortuitous on a text-heavy document. The LlamaParse divergence shows they *will* separate on figure-heavy content — which is the point, not a flaw.
- **Both ground truths are LLM-built**, not human-curated. Each was audited (strong-only stratification; independent Claude-vision pass + text-layer correction) but neither is a gold human transcription. A human GT on either corpus would dominate both and is the obvious next investment if a tie-break between the two experiments were ever needed.

---

## Appendix A — Exact scoreboards used in this analysis

**`PDF parsing test` fair-total, per document, per vendor (info capture %, corrected v2-GT + no-truncation run):**

| Vendor | Alpha (deck) | IAR (report) | SOTER (deck) | All-599 headline |
|---|---:|---:|---:|---:|
| gpt-5 image ◆ | 85.3 | 96.3 | 87.4 | 91.3 |
| Gemini 3.5 Flash | 87.1 | 96.2 | 88.0 | 91.8 |
| gpt-5 file ◆ | 87.0 | 95.0 | 87.3 | 91.0 |
| Gemini 3.1 Flash-Lite | 85.9 | 95.1 | 83.5 | 89.9 |
| Landing AI | 82.2 | 94.3 | 78.6 | 87.4 |
| PyMuPDF | 77.9 | 89.6 | 80.1 | 84.2 |
| LlamaParse | 69.7 | 74.7 | 64.9 | 71.1 |
| Tesseract | 59.7 | 71.0 | 53.0 | 63.8 |

◆ = upper-bound reference (gpt-5 built the GT; same family). Unsupported on IAR: Landing AI 11.6%, across all docs 17.0% (highest of the real parsers).

**`pdf-extraction-audit` combined recall, per document (full GT / strong-only %):**

| Vendor | lastminute | eDreams IAR | FIREBIRD |
|---|---:|---:|---:|
| GPT-5.5 | 92.1 / 87.3 | 91.6 / 88.8 | 94.9 / 94.8 |
| Claude Opus 4.7 | 92.3 / 87.4 | 92.6 / 89.7 | 93.6 / 93.8 |
| Landing AI | 92.6 / 87.2 | 93.6 / 89.5 | 93.1 / 90.6 |
| LlamaParse | 92.0 / 87.0 | 87.8 / 87.2 | 85.9 / 86.8 |

LA self-bias (full − strong): lastminute +5.4, IAR +4.1, FIREBIRD +2.4. Strong-only winners: Claude (lastminute, IAR), GPT (FIREBIRD). Landing AI wins **zero** documents on strong-only GT.

## Appendix B — Provenance

- Shared document proof: `md5 = b4ec6744fc4b929d339dc41455b7e1ca`, 310pp, for both `pdf-extraction-audit/corpus/edreams_iar_fy25.pdf` and `PDF parsing test/Data/IAR_FY25_EN.pdf`.
- This repo's per-page judgments: `results/_fair_total_judging.json` (599 records: doc, page, weight, per-vendor info_recall + unsupported; corrected no-truncation run). Per-document figures recomputed from it for this doc.
- This repo's metric: `scripts/score_fair_total.py`, `scripts/fair_total_report.py` → `results/FAIR_TOTAL.md`. Fair total = Σ(info_recall × page_info_weight) ÷ Σ(page_info_weight); `unsupported` reported separately, **not** subtracted. Truncation correction: `AUDIT_VEND_CAP.md`.
- Audit's authoritative numbers: `/Users/vz/pdf-extraction-audit/FINDINGS.md` (supersedes the older 8-page tier), `VENDOR_STRENGTHS.md`, `runs/_three_doc_full_metrics.json`. Audit metric: per-fact recall, GT = GPT-5.5 + Claude-Sonnet-4.6 vision consensus with Landing AI as disputed-fact tie-breaker.
- This repo's GT audit (twin-bias mitigation): independent Claude-vision pass + text-layer figure correction; see `FINAL_REPORT.md` §9 and `DESIGN.md` §3.
