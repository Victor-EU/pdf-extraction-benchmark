# Enterprise Local Data-Extraction Platform — Architecture

A page-aware PDF extraction pipeline that routes each page to the cheapest
correct engine, then wraps every extracted value in provenance (the
"coordinates") and runs it through enterprise data-governance controls before
it reaches any consumer.

```
╔══════════════════ ENTERPRISE LOCAL DATA-EXTRACTION PLATFORM ══════════════════╗

        ┌─ born-digital text/tables ──► text-layer parser (doesn't invent; ~5% unsup.)
        │                               pdfplumber/pypdf = permissive; classic PDF SDK
PDF ──► classify page ─┼─ figures / charts / diagrams ──► vision LLM (e.g. Gemini Flash)
        └─ scanned / no text layer ───► vision LLM or cloud Document-AI
                                              │
                              low-confidence / high-stakes field
                                              ▼
                                   human-in-the-loop review (with coordinates)
                                              │
        ── every extracted value, auto OR reviewed, flows down ──
                                              ▼
──────────────────────────  TRACEABILITY  LAYER  ───────────────────────────────
  each value is sealed in a provenance record (the "coordinates"):

        value ──┬─ source      doc_id + SHA-256(bytes)        ← immutable origin
                ├─ location     page · bbox(x0,y0,x1,y1) · char_span
                ├─ extractor    engine + model@version  (text │ vision │ DocAI)
                ├─ confidence   text-layer = 1.00 deterministic · vision = scored
                ├─ review       auto │ human-verified  + reviewer id
                └─ run_id       extraction batch + UTC timestamp

  ⇒ click any output cell  →  highlight the exact pixels it was read from
──────────────────────────  DATA GOVERNANCE  LAYER  ────────────────────────────
  classify ─► control ─► account, for every traceable record:

        ├─ classify    PII / PHI / MNPI detection  →  sensitivity tags
        ├─ access      RBAC / ABAC · per-folder write boundaries
        ├─ residency   local-first; only the hosted PARSE call leaves the box
        ├─ retention   TTL + right-to-erasure  (cascades down the lineage DAG)
        ├─ lineage     source → field → derived artifact  (directed graph)
        ├─ audit       append-only, immutable, who-saw-what log
        └─ crypto      encrypted at rest + in transit · key per workspace

  ⇒ every record maps to  →  GDPR · SOC 2 · HIPAA controls
────────────────────────────────────────────────────────────────────────────────
                                              │
                                              ▼
                          governed, traceable records
                   ┌───────────────┼─────────────────┐
                   ▼               ▼                 ▼
               analytics        exports          AI agents
             (dashboards)    (xlsx/md/api)   (RAG w/ citations)

╚════════════════════════════════════════════════════════════════════════════════╝
```

## Layer notes

### Extraction routing
Each page is classified and sent to the cheapest engine that can read it
correctly. Born-digital text/tables go to a text-layer parser (0%
hallucination); figures, charts, and diagrams go to a vision LLM; scanned pages
with no text layer go to a vision LLM or cloud Document-AI. A human-in-the-loop
gate catches low-confidence or high-stakes fields, always with coordinates.

### Traceability layer
Every extracted value — whether produced automatically or human-reviewed — is
sealed in a provenance record. Coordinates are dual-typed: text-layer
extraction yields an exact `char_span`, while vision/DocAI yields a `bbox`. The
`extractor` field pins the engine and model version for reproducibility, and
`confidence` is path-aware (text-layer is deterministic at 1.00; vision is
scored). This is what makes click-to-source possible: any output cell links
back to the exact pixels it was read from.

### Data governance layer
Governance is built **on top of** traceability — lineage, retention cascade,
and audit all depend on the per-value provenance records underneath them.
Right-to-erasure cascades down the lineage DAG; lineage itself is just
provenance records chained `source → field → artifact`. Residency is
local-first and stated honestly: the only egress is the hosted parse call.
Every governed record maps to GDPR, SOC 2, and HIPAA controls.

### Consumers
Governed, traceable records fan out to analytics dashboards, exports
(xlsx/md/api), and AI agents that cite their sources via RAG.
