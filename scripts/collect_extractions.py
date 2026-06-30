#!/usr/bin/env python3
"""Normalize each vendor's raw extraction into a common per-page shape for scoring.

Per page record:
  {doc, page,
   text_tokens:[...], num_tokens:[...],     # for text/numeric recall (dims 1 + finance numbers)
   tables:[ "<table text>", ... ],          # for table fidelity (dim 2)
   figures:[ {kind, content}, ... ],        # for diagram/graph judging (dim 3 + graphs)
   ordered_texts:[ "block", ... ] }         # vendor reading order (dim 4)

Usage: python3 scripts/collect_extractions.py <pymupdf|tesseract|llamaparse|landingai|gpt5_image|gpt5_file>
Output: results/_extract_<vendor>.json
"""
import os, re, sys, json, glob
import fitz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import discover_pdfs

_word_re = re.compile(r"[^\W\d_]+", re.UNICODE)
_num_re = re.compile(r"\d[\d.,%/]*")
RENDER = "ground_truth/render_full"


def norm_words(s):
    return [w.lower() for w in _word_re.findall(s or "") if len(w) > 1]

def norm_nums(s):
    out = []
    for m in _num_re.findall(s or ""):
        t = m.rstrip(".,/").replace(" ", "")
        if re.sub(r"[^\d]", "", t):
            out.append(t)
    return out

def manifest():
    return json.load(open(os.path.join(RENDER, "_manifest.json")))

def pdfs():
    return discover_pdfs()

def rec(doc, page, text="", tables=None, figures=None, ordered=None, extra_nums=""):
    return {"doc": doc, "page": page,
            "text_tokens": sorted(set(norm_words(text))),
            "num_tokens": sorted(set(norm_nums(text) + norm_nums(extra_nums))),
            "tables": tables or [],
            "figures": figures or [],
            "ordered_texts": [re.sub(r"\s+", " ", t).strip()[:160] for t in (ordered or []) if t and t.strip()],
            # untruncated reading-order blocks (text + tables) for full-fidelity vendor .md reconstruction
            "ordered_full": [re.sub(r"\s+", " ", t).strip() for t in (ordered or []) if t and t.strip()]}


def collect_pymupdf():
    out = []
    P = pdfs()
    docs = {}
    for m in manifest():
        doc, page = m["doc"], m["page"]
        if doc not in docs:
            docs[doc] = fitz.open(P[doc])
        pg = docs[doc][page - 1]
        text = pg.get_text("text")
        blocks = [b for b in pg.get_text("blocks") if b[4].strip()]
        blocks.sort(key=lambda b: (round(b[1] / 12), b[0]))
        ordered = [b[4] for b in blocks]
        tables = []
        try:
            for t in pg.find_tables().tables:
                tables.append("\n".join(["\t".join("" if c is None else str(c) for c in row)
                                         for row in t.extract()]))
        except Exception:
            pass
        out.append(rec(doc, page, text=text, tables=tables, ordered=ordered))
    return out


def collect_tesseract():
    """Full-page OCR (born-digital pages re-rasterized). Slow; resumable cache."""
    import pytesseract
    from PIL import Image
    cache = "ground_truth/tesseract_text"
    os.makedirs(cache, exist_ok=True)
    out = []
    for m in manifest():
        doc, page = m["doc"], m["page"]
        cp = os.path.join(cache, f"{doc}__p{page:04d}.txt")
        if os.path.exists(cp):
            text = open(cp).read()
        else:
            text = pytesseract.image_to_string(Image.open(os.path.join(RENDER, m["png"])))
            open(cp, "w").write(text)
        # ordered by OCR line order (already reading-ish)
        ordered = [ln for ln in text.splitlines() if ln.strip()]
        out.append(rec(doc, page, text=text, ordered=ordered))
    return out


def collect_llamaparse():
    """Default reads the `accurate`-mode raw and assembles from typed items (captures
    97-99% of the page md). Set LP_RAW_DIR + LP_USE_PAGE_MD=1 for the agentic-tier re-run:
    that assembles from LlamaParse's own canonical page `md` (the richest representation,
    exactly what the prior pdf-extraction-audit scored at 87.8%). The <3% items-vs-md gap
    is dwarfed by the ~27% accurate→agentic mode gap, so the mode comparison is not
    assembly-confounded; if anything items-assembly slightly flatters accurate's relative
    completeness, making the agentic lift a conservative estimate."""
    raw_dir = os.environ.get("LP_RAW_DIR", "ground_truth/llamaparse/raw")
    use_page_md = os.environ.get("LP_USE_PAGE_MD", "0") == "1"
    out = []
    for doc in discover_pdfs():
        path = f"{raw_dir}/{doc}.json"
        if not os.path.exists(path):
            print(f"  [skip] {doc}: no raw at {path}", file=sys.stderr)
            continue
        d = json.load(open(path))
        for p in d["pages"]:
            page = p["page"]
            if use_page_md:
                md = p.get("md", "") or ""
                tables = [it.get("csv") or it.get("md") or it.get("value") or ""
                          for it in p.get("items", []) if it.get("type") == "table"]
                out.append(rec(doc, page, text=md, tables=tables, figures=[], ordered=[md]))
                continue
            text = p.get("text", "") or ""
            tables, ordered = [], []
            for it in p.get("items", []):
                t = it.get("type")
                val = it.get("value") or it.get("md") or ""
                if t == "table":
                    tables.append(it.get("csv") or it.get("md") or val)
                ordered.append(val if isinstance(val, str) else str(val))
            # LlamaParse (accurate) produces NO figure descriptions
            out.append(rec(doc, page, text=text, tables=tables, figures=[], ordered=ordered))
    return out


_LA_FIG_TABLE = re.compile(r"\btable\b", re.I)
def _la_figure_is_table(txt):
    """Landing AI's ADE classifies a table region containing logos/photos/icons as a
    `figure` chunk whose text holds the FULL table (data + an explicit `table:` block).
    Detect those so table-recovery isn't undercounted — require the word 'table' AND
    structural evidence (bullets / pipes / digits) to avoid crediting prose mentions.
    See memory: pdf_parsing_test_table_metric_artifact."""
    return bool(_LA_FIG_TABLE.search(txt) and
                ("•" in txt or "|" in txt or any(ch.isdigit() for ch in txt)))


def collect_landingai():
    out = []
    for m in manifest():
        doc, page = m["doc"], m["page"]
        f = glob.glob(f"ground_truth/landingai_full/raw/{doc}__p{page:04d}.png.json")
        if not f:
            out.append(rec(doc, page)); continue
        data = json.load(open(f[0])).get("data", {})
        text_parts, tables, figures, ordered = [], [], [], []
        for c in data.get("chunks", []):
            ct = c.get("chunk_type", ""); txt = c.get("text", "") or ""
            if ct == "table":
                tables.append(txt); ordered.append(txt)
            elif ct == "figure":
                figures.append({"kind": "unknown", "content": txt})
                # table rendered AS a figure (photo/logo-embedded) — credit it as a table too
                if _la_figure_is_table(txt):
                    tables.append(txt)
            else:
                text_parts.append(txt); ordered.append(txt)
        out.append(rec(doc, page, text="\n".join(text_parts), tables=tables,
                       figures=figures, ordered=ordered))
    return out


_LA_DPT2_ANCHOR = re.compile(r"<a id='[^']*'></a>")

def _la_dpt2_clean(s):
    s = _LA_DPT2_ANCHOR.sub("", s or "")
    s = s.replace("<::", "").replace("::>", "")
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def collect_landingai_dpt2():
    """DPT-2 (v1/ade/parse) raw -> vendor format, reduced like collect_landingai. New chunk shape:
    top-level `chunks`, each {type, markdown}. DPT-2 adds form-aware types (attestation, scan_code,
    logo) where the legacy model dumped generic `figure`/`text`."""
    out = []
    for m in manifest():
        doc, page = m["doc"], m["page"]
        f = glob.glob(f"ground_truth/landingai_dpt2/raw/{doc}__p{page:04d}.png.json")
        if not f:
            out.append(rec(doc, page)); continue
        data = json.load(open(f[0]))
        text_parts, tables, figures, ordered = [], [], [], []
        for c in data.get("chunks", []):
            ct = c.get("type", "")
            txt = _la_dpt2_clean(c.get("markdown") or c.get("text") or "")
            if not txt:
                continue
            if ct == "table":
                tables.append(txt); ordered.append(txt)
            elif ct in ("figure", "image", "chart", "picture", "logo"):
                figures.append({"kind": "unknown", "content": txt})
                if _la_figure_is_table(txt):
                    tables.append(txt)
            else:  # text, marginalia, attestation, scan_code, ...
                text_parts.append(txt); ordered.append(txt)
        out.append(rec(doc, page, text="\n".join(text_parts), tables=tables,
                       figures=figures, ordered=ordered))
    return out


def _block_text(b):
    """Grader-facing rendering of one block. Forms add two structured block types whose
    binding must survive into the page text: `field` (label->value) and `choice`
    (checkbox/radio label + checked/unchecked state). Robust to models that populate the
    structured keys but leave `content` empty (and vice-versa)."""
    t = b.get("type")
    content = (b.get("content") or "").strip()
    if t == "field":
        lbl = (b.get("field_label") or "").strip()
        val = (b.get("field_value") or "").strip()
        if content:
            return content
        return f"{lbl}: {val}".strip().strip(":").strip() if (lbl or val) else ""
    if t == "choice":
        lbl = (b.get("choice_label") or "").strip()
        state = (b.get("choice_state") or "").strip().lower()
        mark = "x" if state == "checked" else " "
        if content:
            return content
        return f"[{mark}] {lbl}" if lbl else ""
    return content


def _from_blocks(blocks):
    text_parts, tables, figures, ordered = [], [], [], []
    for b in blocks:
        t = b.get("type")
        if t == "table":
            c = (b.get("content") or "")
            tables.append(c); ordered.append(c)
        elif t == "figure":
            figures.append({"kind": b.get("figure_kind", "unknown"),
                            "content": b.get("content", "") or ""})
        else:  # text, heading, field, choice, marginalia, other
            s = _block_text(b)
            if s:
                text_parts.append(s); ordered.append(s)
    return text_parts, tables, figures, ordered


_LP_IMG = re.compile(r"!\[[^\]]*\]\([^)]*\)")           # empty image placeholders LiteParse emits
_LP_PIPEROW = re.compile(r"^\s*\|.*\|\s*$")

def _lp_clean(md):
    """Drop LiteParse's empty `![](image_pNN_K.png)` placeholders (it is vision-blind — these carry
    no content) and collapse the blank lines they leave behind."""
    md = _LP_IMG.sub("", md or "")
    return re.sub(r"\n{3,}", "\n\n", md).strip()

def _lp_tables(md):
    """Extract contiguous markdown pipe-table blocks so table recovery is credited like other
    vendors. A block is >=2 consecutive pipe rows (header + at least one row / separator)."""
    out, cur = [], []
    for ln in (md or "").splitlines():
        if _LP_PIPEROW.match(ln):
            cur.append(ln.strip())
        else:
            if len(cur) >= 2:
                out.append("\n".join(cur))
            cur = []
    if len(cur) >= 2:
        out.append("\n".join(cur))
    return out

def collect_liteparse():
    """LiteParse (run-llama OSS, LlamaParse core minus VLM): per-page reconstructed MARKDOWN from the
    BORN-DIGITAL PDF (scripts/liteparse_run.py). Vision-blind, so figures=[] (placeholders stripped).
    Serve the whole page markdown as one ordered block (ordered_full=md) — the same page-md path as
    LlamaParse's agentic representation — and surface its heuristic pipe tables."""
    raw = "ground_truth/liteparse/raw"
    out = []
    for m in manifest():
        doc, page = m["doc"], m["page"]
        p = os.path.join(raw, f"{doc}__p{page:04d}.md")
        md = _lp_clean(open(p).read()) if os.path.exists(p) else ""
        out.append(rec(doc, page, text=md, tables=_lp_tables(md), figures=[], ordered=[md]))
    return out


def collect_mistral():
    """Mistral OCR-4 (advanced config) raw per-page response -> vendor format. The page markdown
    (tables inlined as HTML, image placeholders stripped) is the single ordered block (-> ordered_full,
    like the LlamaParse page-md / LiteParse path); each annotated image becomes a figure {kind, content}
    (parallel to collect_landingai's figure chunks) so OCR-4 is fairly credited on the form graphics
    (logos, stamps, scanned regions). Reduction lives in mistral_common.reduce_page, shared with the
    runner + input A/B so they cannot diverge. Table-cell text + figure descriptions join the numeric
    pool (form values / amounts live there)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import mistral_common as M
    raw = "ground_truth/mistral/raw"
    out = []
    for m in manifest():
        doc, page = m["doc"], m["page"]
        cp = os.path.join(raw, f"{doc}__p{page:04d}.json")
        if not os.path.exists(cp):
            print(f"  [skip] {doc} p{page}: no raw at {cp}", file=sys.stderr)
            out.append(rec(doc, page)); continue
        resp = json.load(open(cp))
        pg = (resp.get("pages") or [{}])[0]
        md, tables, figures = M.reduce_page(pg)
        extra_nums = "\n".join(tables) + "\n" + "\n".join(f["content"] for f in figures)
        out.append(rec(doc, page, text=md, tables=tables, figures=figures,
                       ordered=[md], extra_nums=extra_nums))
    return out


def collect_pulse():
    """Pulse (runpulse.com, advanced config: pulse-ultra-2 + refine + figure extraction) raw
    per-page response -> vendor format. The top-level page markdown (tables already inline, checkbox
    glyphs preserved in reading order) is the single ordered block (-> ordered_full, like the
    LlamaParse page-md / LiteParse / Mistral path); each annotated image becomes a figure
    {kind, content}. Reduction lives in pulse_common.reduce_response, shared with the runner so they
    cannot diverge. Reconstructed table-cell text + figure descriptions join the numeric pool."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pulse_common as P
    raw = "ground_truth/pulse/raw"
    out = []
    for m in manifest():
        doc, page = m["doc"], m["page"]
        cp = os.path.join(raw, f"{doc}__p{page:04d}.json")
        if not os.path.exists(cp):
            print(f"  [skip] {doc} p{page}: no raw at {cp}", file=sys.stderr)
            out.append(rec(doc, page)); continue
        resp = json.load(open(cp))
        md, tables, figures = P.reduce_response(resp)
        extra_nums = "\n".join(tables) + "\n" + "\n".join(f["content"] for f in figures)
        out.append(rec(doc, page, text=md, tables=tables, figures=figures,
                       ordered=[md], extra_nums=extra_nums))
    return out


def collect_gpt5(mode):
    data = json.load(open(f"results/_openai_{mode}_extract.json"))
    out = []
    for r in data:
        tp, tb, fg, od = _from_blocks(r.get("blocks", []))
        # include table cell text + figure graph-data in numeric pool (finance numbers live there)
        extra_nums = "\n".join(tb) + "\n" + "\n".join(f["content"] for f in fg)
        out.append(rec(r["doc"], r["page"], text="\n".join(tp), tables=tb,
                       figures=fg, ordered=od, extra_nums=extra_nums))
    return out


def collect_gemini(slug):
    """Gemini emits the SAME block schema as gpt-5 (via gemini_extract.py), so reuse _from_blocks."""
    data = json.load(open(f"results/_gemini_{slug}_extract.json"))
    out = []
    for r in data:
        tp, tb, fg, od = _from_blocks(r.get("blocks", []))
        extra_nums = "\n".join(tb) + "\n" + "\n".join(f["content"] for f in fg)
        out.append(rec(r["doc"], r["page"], text="\n".join(tp), tables=tb,
                       figures=fg, ordered=od, extra_nums=extra_nums))
    return out


COLLECTORS = {
    "pymupdf": collect_pymupdf, "tesseract": collect_tesseract,
    "llamaparse": collect_llamaparse, "landingai": collect_landingai,
    "landingai_dpt2": collect_landingai_dpt2,
    "liteparse": collect_liteparse,
    "mistral": collect_mistral,
    "pulse": collect_pulse,
    "gpt5_image": lambda: collect_gpt5("image"), "gpt5_file": lambda: collect_gpt5("file"),
    "gemini_flash": lambda: collect_gemini("gemini_flash"),
    "gemini_flash_lite": lambda: collect_gemini("gemini_flash_lite"),
    "gemini_flash_file": lambda: collect_gemini("gemini_flash_file"),
    "gemini_flash_lite_file": lambda: collect_gemini("gemini_flash_lite_file"),
}


def main():
    vendor = sys.argv[1]
    out = COLLECTORS[vendor]()
    out.sort(key=lambda r: (r["doc"], r["page"]))
    json.dump(out, open(f"results/_extract_{vendor}.json", "w"))
    nfig = sum(len(r["figures"]) for r in out)
    ntab = sum(len(r["tables"]) for r in out)
    print(f"{vendor}: {len(out)} pages | total figures={nfig} tables={ntab} | -> results/_extract_{vendor}.json")


if __name__ == "__main__":
    main()
