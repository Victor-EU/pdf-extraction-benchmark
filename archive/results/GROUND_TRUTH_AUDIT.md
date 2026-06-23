# Ground-Truth Audit — is the answer key trustworthy?

**Trigger:** suspicion that strong parsers "only" scoring 66% (Landing AI) / 80% (GPT-5) implies the
key is wrong. **Method:** use **GPT-5** as a genuinely independent *third* vote (it had no hand in the
key) to triangulate against Claude vision + Landing AI, then **re-examine the contested pages by eye**.

## TL;DR verdict
The key is **sound, not broadly wrong** — but the suspicion correctly surfaces two real facts:
1. **The key is vision-anchored, not co-authored.** `final == vision` on **94%** of pages;
   `final == landing_ai` on only **66%**. In the 227 tiebreaks, vision won **198**, Landing AI **29**.
   So wherever the two original sources disagreed, the key ≈ "what Claude vision said."
2. **The one genuinely soft spot is the `Mixed` category** (112 pages, 19%). It is intrinsically
   subjective and rests almost entirely on vision's eye (see below).

Everything else holds up. **Even the maximal possible correction leaves the rankings unchanged** and
Landing AI still mediocre — so the key is *not* the reason these parsers score where they do.

## Evidence the core is solid
| Slice | GPT-5 (independent) agreement with key |
|---|---:|
| **Core: 365 pages where vision == Landing AI** (locked) | **88.2%** |
| Contested: 227 tiebreak pages | 70.0% |

Where two sources already agreed, a third independent model confirms the key **88%** of the time — the
easy majority of the key is rock-solid. The fragility is confined to the tiebreak set.

**Gross errors: ~0.** Of GPT's 115 disagreements, only **2** involve confusing the "easy" functional
categories (Cover/Divider, Image/Photo) with a content type — and both are defensible "by function"
boundary calls (IAR p5 a ToC page → Cover/Divider; Alpha p94 one of the 2 Image/Photo pages → Mixed).
There is **no** case of, say, a table labelled a cover. The entire disagreement space is *boundary fuzz*.

## The real soft spot: `Mixed` is a coin-flip category
On the **112 pages the key calls Mixed**, how many does each source independently call Mixed?

| Source | calls it Mixed | note |
|---|---:|---|
| Claude vision | **108 / 112 (96%)** | vision effectively *defines* Mixed in the key |
| Landing AI | 51 / 112 (46%) | independent |
| GPT-5 image | 54 / 112 (48%) | independent |
| GPT-5 file | 36 / 112 (32%) | independent |

Two independent frontier systems reproduce the key's "Mixed" only **~half** the time. "Mixed = no
dominant type" is a judgment, not a structural fact — so it has a low inter-annotator ceiling and the
key's Mixed labels hang almost entirely on one grader (vision). GPT's disagreements confirm this:
**86%** of its 115 errors involve Mixed, and they go **both ways** — 58 are key-Mixed/GPT-other, 41 are
GPT-Mixed/key-other. The boundary is noisy in both directions, i.e. unstable, not biased.

## Why the parsers "only" hit 66–80% — it is NOT broad key error
I re-examined the **19 pages where GPT-image, GPT-file AND Landing AI all converge on a label the key
rejects** (the strongest possible "key is wrong" signal — the key standing alone against three
independent votes). Looking at each page myself:

- **~6 the key is RIGHT and all three parsers are wrong — for the *same* reason.** GPT and Landing AI
  share a **text-centric bias**: they over-call **Text** when a page has lots of prose, missing
  (a) **matrix/table structure** whose cells contain prose (SOTER p21 — a 5×2 product comparison grid,
  correctly Table), and (b) **large photos** that make a page Mixed (SOTER p32/p37 case-studies = big
  photo + text cards; IAR p38 = prose + bar-chart + table, a textbook Mixed). On these, vision was the
  *only* source that read the structure correctly — so the "vision anchoring" is partly **justified**,
  not a defect.
- **~5 the key is genuinely weaker than the consensus** (real tiebreak slips, all in the
  Text/Table/Chart-vs-Mixed zone): e.g. **IAR p260** (3 financial tables dominate → key said Mixed,
  should be **Table**); **IAR p89** (prose + org-chart → key said Chart/Diagram, better **Mixed**);
  IAR p99 / p221 (lean Mixed). These are worth correcting.
- **~8 genuine coin-flips** where no label is clearly right (IAR p196, p282, p158, Alpha p120, …).

So strong parsers underperform for two compounding reasons that have **nothing to do with a broken key**:
**(1)** ~19% of pages are the intrinsically-subjective Mixed category (a ceiling that caps everyone),
and **(2)** GPT and Landing AI share a structural blind spot (text-centrism) that vision does not.

## Robustness: the ranking survives even maximal correction
Re-scoring every solution after flipping **all 19** strict-consensus suspects to the consensus label
(an over-correction — ~6 of the 19 the key was actually right):

| Solution | v1 key | max-corrected | Δ |
|---|---:|---:|---:|
| GPT-5 image | 80.8% | 84.0% | +3.2 |
| GPT-5 file | 80.0% | 83.1% | +3.2 |
| Landing AI* | 65.8% | 68.9% | +3.2 |
| PyMuPDF | 45.4% | 45.7% | +0.3 |
| Tesseract | 45.1% | 45.2% | +0.2 |

Realistic correction (only the ~5–6 genuine slips) is **≈ +1.5%** → GPT-5 ≈ 82%, Landing AI ≈ 67%.
Rankings are unchanged under either scenario. **Landing AI stays mediocre at semantic page-categorization
no matter how the boundary is graded** — it is a strong *extractor* but a weak *classifier*; the
structural tools stay at 45% (their errors are gross, not boundary, so corrections don't help them).

## How to read every score honestly
Report **with and without Mixed**, because Mixed is a soft ~50% inter-annotator category:

| Solution | overall | **excluding Mixed** (487 pages) |
|---|---:|---:|
| GPT-5 image | 80.8% | **88.3%** |
| GPT-5 file | 80.0% | **91.0%** |

The realistic ceiling on this 6-way taxonomy is ~**85–90%** (Mixed caps it). GPT-5 is already near it;
its remaining gap is mostly defensible boundary calls, not real misses.

## Corrections applied → answer key v2
Five corrections were proposed; **a careful rubric re-read cut it to three.** v1 stays frozen
(`final_answer_key.json`); v2 is `final_answer_key_v2.json` (each corrected page keeps a `v1_label` +
`audit_reason`). All scorecards now report v2 (v1 in parentheses).

| Page | v1 | → v2 | Why |
|---|---|---|---|
| IAR p260 | Mixed | **Table** | 3 financial tables dominate; rubric: financial statements = Table, and they're the dominant type |
| IAR p89 | Chart/Diagram | **Mixed** | *Standalone* prose (Corp Governance + Shareholder Meetings) + org-chart, neither >60% — prose is not diagram labels |
| IAR p99 | Text | **Mixed** | Standalone prose + 3-node diagram + full-width flow bar (~40% non-prose) — too much structure for pure Text |

**Two proposals were DROPPED after re-examination** (the discipline that "deep think" demands):
- **SOTER p84 — kept Chart/Diagram.** The rubric *explicitly* lists "flow/process/**chevron** diagrams"
  and "a page organized as a process diagram with bullet annotations is Chart/Diagram (the bullets are
  diagram labels, not standalone prose)." That's exactly this page. The key is right; GPT/Landing AI's
  "Text" is the text-centric bias the rubric warns against. Overturning it would *violate* the rubric.
- **IAR p221 — kept Text.** The two tables are compact reference grids; the "For OpEx" prose is the
  page's substance. The `my_review` Text call is defensible, not clearly wrong → not overturned.

### Impact of v2 (rankings unchanged, deltas tiny)
| Solution | v1 | v2 | excl-Mixed (v2) |
|---|---:|---:|---:|
| GPT-5 image | 80.8% | **81.3%** | 88.7% |
| GPT-5 file | 80.0% | 80.5% | 91.4% |
| Landing AI* | 65.8% | 66.3% | 70.8% |
| PyMuPDF | 45.4% | 45.2% | 51.0% |
| Tesseract | 45.1% | 44.9% | 50.8% |

(Structural tools dip 0.2 because 2 corrections moved pages to Mixed, which they almost never predict.)

## Second audit — LlamaParse as an independent 4th vote (structural, table-biased)
**Trigger:** add LlamaParse (LlamaCloud, another SOTA parser) as a *4th* independent vote and re-stress
the key. LlamaParse is structurally different from the prior voters: a **table-centric** extractor (it
parses charts *into tables*) with **no chart/diagram type** and useless image signal (full-page
background rasters). Its errors are gross (Chart→Table), so it can't adjudicate fine boundary calls —
but its **dedicated table detector** is a genuinely new structural check the LLM voters couldn't give.

**What the 4th vote confirms (per-category reproduction of the key):**
| key category | GPT-img | GPT-file | Landing AI | **LlamaParse** | read |
|---|---:|---:|---:|---:|---|
| Table (127) | 92% | 92% | 72% | **95%** | **strongly vindicated** — a dedicated table detector confirms the key's tables (incl. borderless financials) |
| Cover/Divider (55) | 98% | 98% | 27% | **82%** | **newly vindicated** — LlamaParse recovers it from pure sparsity *where Landing AI failed* |
| Chart/Diagram (152) | 86% | 89% | 82% | 0% | confirmed by all who *can see* charts; LlamaParse's 0% is its own blindness, not key evidence |
| Text (150) | 86% | 91% | 74% | 71% | solid |
| **Mixed (113)** | 50% | 34% | 47% | **12%** | a **4th** source under-reproduces it — Mixed remains the one soft, vision-anchored category |

**Strongest "key is wrong" signal — 6 pages where all 4 independent sources unanimously reject the key.**
I re-rendered each at high resolution and adjudicated by eye:
- **5/6 the key is RIGHT and all four parsers share a blind spot:** IAR p173 (prose + big-number KPI
  infographic cards + pull-quote = textbook Mixed), SOTER p32 (large case-study photo + 3 text boxes =
  Mixed), SOTER p84 (chevron process diagram — rubric *explicitly* = Chart/Diagram), IAR p158/p168
  (prose + a real secondary cycle/process diagram = defensible Mixed). The text-extractors flatten
  photo/infographic/diagram structure to **Text** — the documented correlated bias.
- **1/6 the key was genuinely wrong → fixed:** **IAR p221** (key said Text). High-res shows the right
  half is two stacked Yes/No EU-taxonomy disclosure tables (nuclear/fossil-gas activities) + a top-left
  proportion table (~57–60% of the page); the "For OpEx" prose is a secondary ~20% note. **Tables
  dominate → Table.** The v2 "Text" was an over-eager `my_review` override against *both* original
  sources (vision said Mixed, Landing AI said Table — neither said Text); all four independent re-votes
  say Table. Corrected in **v3**.

This is the discipline working twice over: the 4th vote *confirmed* the key on every structural category
(and added fresh independent backing for Table and Cover/Divider), reinforced that Mixed is the lone soft
spot, and surfaced exactly one real error — which I had introduced myself. **Naive 4-source majority would
have wrongly flipped 5 legitimate Mixed/Chart pages to Text** (proving again: do not re-grade by vote).

### Answer key v3 (`final_answer_key_v3.json`, v2 frozen)
One correction on top of v2: **IAR p221 Text → Table** (`v2_label` + `audit_reason` retained per page).
Re-scored, rankings unchanged, deltas ≤0.2%:

| Solution | v2 | v3 |
|---|---:|---:|
| GPT-5 image | 81.3% | **81.5%** |
| GPT-5 file | 80.5% | 80.6% |
| Landing AI* | 66.3% | 66.4% |
| **LlamaParse** | 47.9% | **48.1%** |
| PyMuPDF | 45.2% | 45.1% |
| Tesseract | 44.9% | 44.9% |

## Recommendations
1. **Trust the key** for the 365-page agreement core and all non-Mixed categories (Cover/Divider 99% F1,
   Table, Chart, Text are clean). It is vision-anchored *by merit* — vision is the strongest single
   classifier on the structure-vs-prose calls the other tools miss.
2. **Treat `Mixed` as soft.** Always report excl-Mixed alongside overall. Consider whether the benchmark
   even needs a "Mixed" bucket, or whether such pages should be labelled by their *primary* type.
3. **Use v2 going forward**; v1 retained for audit. The 3 corrections are documented per-page in v2.
4. Do **not** re-grade by naive 3-source majority vote — it would *delete* legitimate Mixed/photo/matrix
   pages that only vision detects (proven on SOTER p21/p32/p37, IAR p38), degrading the key.
