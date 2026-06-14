# Solution Comparison — page-category accuracy vs the answer key

Scored against **answer key v3** (v2's 3 corrections + 1 LlamaParse-surfaced correction, IAR p221
Text→Table; see `GROUND_TRUTH_AUDIT.md`). v2 overall in parentheses — deltas tiny, rankings unchanged.

| Solution | Overall acc | excl-Mixed | Macro-F1 | Speed | Cost | Notes |
|---|---:|---:|---:|---:|---:|---|
| **OpenAI gpt-5 — image** (page PNG → LLM) | **81.5%** (81.3) | 88.9% | **79.6%** | 4.12 s/page | $0.0030/pg ($1.81/599) | **fair / non-circular** ✅ |
| **OpenAI gpt-5 — file** (1-pg PDF → LLM) | 80.6% (80.5) | **91.5%** | 73.2% | 6.98 s/page | $0.0033/pg ($2.00/599) | **fair / non-circular** ✅ |
| **LlamaParse** (LlamaCloud, accurate mode → structural reduce) | 48.1% (47.9) | 50.7% | 35.9% | **0.63 s/page** | **$0** (free tier; 0 credits) | **fair / non-circular** ✅ — strong extractor, weak classifier |
| **PyMuPDF** (heuristic classifier) | 45.1% (45.2) | 50.8% | 41.5% | **0.11 s/page** | **$0** (local) | fair / non-circular |
| **Tesseract OCR** (heuristic classifier) | 44.9% (44.9) | 50.8% | 39.5% | 1.18 s/page | **$0** (local) | fair / non-circular |
| Landing AI ADE | 66.4%* (66.3) | 70.9% | 55.2%* | 16.6 s/page | paid (per-page) | *CIRCULAR — co-authored key, inflated upper bound |
| Claude vision | ~100%* | — | — | seconds/page (LLM) | paid (tokens) | *authored key; not a fair self-score |

> **Ground-truth audited twice** (see `GROUND_TRUTH_AUDIT.md`). Using GPT-5 (3rd vote) **and now
> LlamaParse (4th, structural, table-biased vote)** to triangulate: the key is sound. LlamaParse's
> dedicated table detector **independently confirms the key's Table category at 95%** (incl. borderless
> financial statements PyMuPDF missed) and recovers **Cover/Divider at 82%** from pure sparsity —
> vindicating both categories, the latter exactly where Landing AI had failed (27%). It IS vision-anchored
> (94%==vision), and `Mixed` is a soft category a **4th** independent source now under-reproduces (12%).
> 6 pages had all-4-sources-vs-key consensus; on high-res inspection **5/6 confirm the key** (shared
> photo/infographic/chevron blindness) and exactly **1** was a real error (p221, an over-eager v2
> my_review override) → fixed in v3. Rankings unchanged under every key version.

**OpenAI, PyMuPDF, Tesseract are all fair, non-circular benchmarks** (none helped build the key).
The frontier-LLM solution (gpt-5) is the standout: it **beats the structural tools by ~35 points
AND clears the circular Landing-AI upper bound** — while staying cheap ($1.81 for all 599 pages) and
the only honest LLM read we have (Claude vision co-authored the key, so it can't be scored fairly).

## OpenAI gpt-5 — two input methods, deep-dive
OpenAI has **no dedicated parsing/OCR service**; "parsing" = handing the page to a vision LLM. We
tested BOTH ways of doing that, same model / prompt / 6-category Structured Output, varying only input:
- **image** — send our rendered PNG (LLM vision on a raster).
- **file** — send the single-page PDF; OpenAI's native ingestion extracts the **text layer + a page
  image** itself. These are born-digital PDFs, so the text layer is real, not OCR.

| Cut | image | file | read |
|---|---:|---:|---|
| Overall (599) | **80.8%** | 80.0% | image edges it |
| **Excluding Mixed** (487 pages) | 88.3% | **91.0%** | **file wins on clear-cut pages** |
| Macro-F1 | **79.1%** | 72.6% | image more balanced |
| Mixed recall | **48%** | 32% | file over-calls Text on Mixed |
| Chart/Diagram F1 | 88% | **91%** | text layer disambiguates chart labels |
| Speed | **4.1 s/pg** | 7.0 s/pg | file pays to extract+ship text |
| Cost / 599 | **$1.81** | $2.00 | ~same |

**The text layer is a double-edged sword.** Feeding the born-digital text (file mode) *sharpens*
unambiguous content-type calls — 91% excluding-Mixed, best Chart/Table disambiguation — but it makes
pages "look textual," so on genuinely **Mixed** pages the model collapses to **Text** (Mixed recall
48%→32%; Mixed→Text confusions 33→49). That single bias flips the *overall* ranking to image-only.
Takeaway: if you only need the dominant type on clean pages, **file mode**; if Mixed/borderline pages
matter, **image mode**. Either way ~80% and ~$2/run.

### Where gpt-5 (image) still errs — and whether the errors are "real"
- **86% of all 115 image errors involve the Mixed category** (true-Mixed or predicted-Mixed). Mixed is
  "no dominant type" — a subjective judgment, not a structural property; *every* method's weakest cell.
- GPT is **calibrated**: of 115 errors only 28 were self-rated "high" confidence; the rest "med/low".
- The non-Mixed errors are mostly **genuine taxonomy boundary disputes the key itself resolved by
  tiebreak** — e.g. a grid of boxed SDG cells (Table vs Chart/Diagram), a KPI infographic (Chart vs
  Table), a SWOT-as-2×2 (Chart vs Text). On several, gpt-5 matches *one* of the two original key
  authors (vision or Landing AI) and just lands on the losing side of a close call — i.e. defensible,
  not a clean miss. Per-category: **Cover/Divider 99% F1, Table 88%, Chart 88%, Text 81%**; Mixed 52%.
- Per-doc (image): Alpha 86% · SOTER 80% · IAR 78%.

### Ensemble signal (free, no extra calls)
The two modes **agree on 86% of pages, and when they agree they're 86% correct**; on the 83
disagreements it's a near coin-flip (image right 40, file right 35, neither 8). So mode-agreement is a
usable confidence flag: trust the 516 agreed pages, route the 83 disagreements to review.

## LlamaParse (LlamaCloud) — SOTA extractor, weak page-classifier
LlamaParse is a SOTA document-parsing service (parse-to-markdown + structured layout). Like Landing AI
ADE and PyMuPDF, it isn't a page-classifier, so we reduce its per-page structural output to a dominant
6-category label (area-dominant rule, thresholds from feature semantics — NOT key-fitted; mirrors the
Landing AI reducer). We parsed all 3 PDFs once in **accurate mode** (599 pages, **0 credits / free tier**,
~377s throughput; ~0.63 s/page). Result: **48.1%** — right alongside the free structural tools, far
below the gpt-5 LLM (~81%) and below Landing AI (66%).

| LlamaParse per-category (v3) | Recall | Precision | F1 | Read |
|---|---:|---:|---:|---|
| Cover/Divider | 82% | 69% | 75% | **best** — sparse text + no table structure is a clean structural signal |
| Table | **95%** | 35% | 52% | dedicated table detector nails real tables (incl. borderless financials)… |
| Text | 72% | 66% | 69% | solid on prose-dominant pages |
| Mixed | 12% | 52% | 20% | table bias swallows Mixed pages → Table |
| **Chart/Diagram** | **0%** | 0% | 0% | **fatal gap — see below** |
| Image/Photo | 0% | — | — | only 2 pages; full-page background rasters make `images` useless |

**Two structural facts define LlamaParse's ceiling:**
1. **No chart/diagram type — in any mode.** The `charts` array is empty on all 599 pages even in
   **agentic/premium** mode (tested on 8 known chart pages: all parsed as text/**table**/images). LlamaParse
   parses a chart's axis data *into a table*, so **86% (131/152) of Chart/Diagram pages collapse to Table**
   and the rest to Text. Chart/Diagram (25% of the corpus) is unrecoverable → that alone caps accuracy ~75%.
   Premium mode would **not** fix this (it just re-parses into tables/text and converges toward an LLM read,
   adding circularity vs the vision-anchored key) — so the structural `accurate` number is the honest one.
2. **Every slide has a full-page background raster** (`big_img==1.0` on all 599 pages), so the `images`
   field carries zero photo/cover signal and is dropped. Classification runs on **text vs table area only**.

Net: LlamaParse is **table-centric** (over-calls Table — 95% Table recall but only 35% precision because
charts pile in), a different bias from gpt-5/Landing AI's **text-centrism**. It's an excellent *extractor*
(table detection, markdown) but, used as a page *classifier*, it lands at structural-tool level. SOTA at
extraction ≠ good at semantic page categorization.

## Tesseract vs PyMuPDF — same accuracy, very different tool
Tesseract (45.1%) ≈ PyMuPDF (45.4%) on accuracy, but **PyMuPDF dominates it**: ~11× faster
(0.11s vs 1.18s/page) and structurally better-suited. Key facts:
- Tesseract is a pure **OCR engine**: it rasterizes the page and recovers only **text + word
  boxes** — discarding the PDF's native vector/table/image structure that PyMuPDF reads for free.
  On these **born-digital** PDFs that's wasteful (the text layer already exists) and lossy.
  Tesseract's real niche is **scanned/image-only** PDFs — none of these 3 are scanned.
- The two free tools agree with **each other only 39%** — they make *different* errors (PyMuPDF
  via vectors/`find_tables`; Tesseract via text density), so an **ensemble** could beat either.
- Per category: Tesseract is best at **Cover/Divider** (F1 77%, precision 95% — sparse text is
  obvious) but its **Chart/Diagram is a catch-all sink**: 144 non-chart pages (49 Table, 51 Mixed,
  26 Text, 17 Cover) dumped there because OCR sees "a big non-text region" and can't tell what it
  is. PyMuPDF's `find_tables` gives it far better **Table precision** (79% vs 33%).
- Per-doc: SOTER 61% (Tesseract's best — sparse pitch slides), IAR 40%, Alpha 42%.

## PyMuPDF — per-category (fair number)
| Category | Recall | Precision | F1 | Read |
|---|---:|---:|---:|---|
| Cover/Divider | 58% | 84% | 69% | best — sparse/big-image pages are structurally obvious |
| Chart/Diagram | 53% | 76% | 63% | vector-density signal works well |
| Text | 62% | 43% | 51% | catches prose, but over-predicts (table/mixed leak in) |
| Table | 33% | 79% | 47% | high precision, low recall (see below) |
| Mixed | 21% | 20% | 20% | weak — "no dominant type" isn't a structural feature |
| Image/Photo | 0% | 0% | 0% | only 2 pages; folds into Cover/Divider by design |

Per-document: Alpha 45% · IAR 42% · SOTER 54%.

## Why PyMuPDF tops out ~45%
1. **Borderless tables (the #1 error): 49 true tables → predicted Text.** PyMuPDF's
   `find_tables()` keys on ruling lines; whitespace-aligned financial statements have none,
   so they read as prose. Pushing `find_tables(strategy="text")` would help but over-detects
   and slows it — and tuning to recover these would overfit this 599-page set.
2. **Mixed is not a structural property.** "Two substantial content types, none dominant" needs
   semantic judgment; features can only approximate it (caught via ≥2 strong signals → 21% recall).
3. **Cover/Divider vs Image/Photo is functional**, invisible to structure — handled by biasing
   low-text big-image pages to Cover/Divider (matches the rubric; Image/Photo is only 2/599).

## Method notes (fairness)
- Thresholds set from first-principles feature semantics, **NOT** fitted to the answer-key labels.
- One disclosed design iteration after v1 (35.1%): excluded table-cell text from the prose-Text
  signal (cell text isn't prose) and required ≥2 strong signals for Mixed. Both are mechanism
  fixes, not label-tuning.

## Takeaway
PyMuPDF is **~150× faster and $0 to run** (AGPL-licensed, *not* free for proprietary use — see `../FINAL_REPORT.md` §6 note ¹), but recovers semantic page categories at ~45% — it is a
structural extractor, not a classifier. Best where structure is unambiguous (charts, dividers)
and high-precision on tables it does detect; weak on Mixed and borderless tables. Good as a
cheap first-pass / pre-filter; not a standalone categorizer at this accuracy.
