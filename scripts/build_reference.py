#!/usr/bin/env python3
"""Build the EXTRACTION ground-truth reference per page (vendor-neutral).

For each page produces the target each vendor's extraction is graded against:
  - ref_tokens : normalized text tokens = born-digital TEXT LAYER  ∪  OCR of image regions
                 (so raster-baked text counts; fair to vision/OCR tools, de-circularizes PyMuPDF)
  - ref_numbers: numeric tokens (financial fidelity target)
  - reading_order: text-layer blocks in natural (top->bottom, left->right) order (spatial target)
  - image_regions: normalized bboxes of sizeable rasters (figure candidates / image-text source)
  - counts: how many ref tokens came from the text layer vs from image OCR

Output: ground_truth/extraction_ref/{doc}__p{page:04d}.json
"""
import os, re, sys, json, glob
import fitz
import pytesseract
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import discover_pdfs

OUT = "ground_truth/extraction_ref"
RENDER = "ground_truth/render_full"
MIN_IMG_FRAC = 0.04   # OCR only rasters >=4% of page area

_word_re = re.compile(r"[^\W\d_]+", re.UNICODE)      # alphabetic tokens
_num_re = re.compile(r"\d[\d.,%/]*")                  # numeric tokens


def norm_words(s):
    return [w.lower() for w in _word_re.findall(s or "") if len(w) > 1]


def norm_nums(s):
    out = []
    for m in _num_re.findall(s or ""):
        t = m.rstrip(".,/").replace(" ", "")
        digits = re.sub(r"[^\d]", "", t)
        if len(digits) >= 1:
            out.append(t)
    return out


def page_image_regions(page):
    W, H = page.rect.width, page.rect.height
    regs = []
    for im in page.get_image_info():
        b = im.get("bbox")
        if not b:
            continue
        a = abs((b[2] - b[0]) * (b[3] - b[1])) / (W * H) if W * H else 0
        if a >= MIN_IMG_FRAC:
            regs.append((b, a))
    return regs


def ocr_regions(doc, page_no, regions, page):
    """Crop each image region from the render PNG and OCR it."""
    png = os.path.join(RENDER, f"{doc}__p{page_no:04d}.png")
    if not os.path.exists(png) or not regions:
        return []
    img = Image.open(png)
    PW, PH = img.size
    W, H = page.rect.width, page.rect.height
    sx, sy = PW / W, PH / H
    toks = []
    for (b, _a) in regions:
        crop = img.crop((max(0, int(b[0]*sx)), max(0, int(b[1]*sy)),
                         min(PW, int(b[2]*sx)), min(PH, int(b[3]*sy))))
        if crop.width < 8 or crop.height < 8:
            continue
        try:
            txt = pytesseract.image_to_string(crop)
        except Exception:
            txt = ""
        toks.append(txt)
    return toks


def main():
    os.makedirs(OUT, exist_ok=True)
    pdfs = discover_pdfs()
    manifest = json.load(open(os.path.join(RENDER, "_manifest.json")))
    by_doc = {}
    for m in manifest:
        by_doc.setdefault(m["doc"], []).append(m["page"])

    done = 0
    for doc, pages in by_doc.items():
        d = fitz.open(pdfs[doc])
        for page_no in sorted(pages):
            outp = os.path.join(OUT, f"{doc}__p{page_no:04d}.json")
            if os.path.exists(outp):
                done += 1; continue
            page = d[page_no - 1]
            W, H = page.rect.width, page.rect.height
            # text layer
            tl_text = page.get_text("text")
            tl_words = set(norm_words(tl_text))
            tl_nums = norm_nums(tl_text)
            # reading order: blocks sorted top->bottom, left->right
            blocks = page.get_text("blocks")
            blocks = [b for b in blocks if b[4].strip()]
            blocks.sort(key=lambda b: (round(b[1] / 12), b[0]))
            reading_order = [re.sub(r"\s+", " ", b[4]).strip()[:160] for b in blocks]
            # image-region OCR
            regs = page_image_regions(page)
            ocr_texts = ocr_regions(doc, page_no, regs, page)
            img_words = set()
            img_nums = []
            for t in ocr_texts:
                img_words |= set(norm_words(t))
                img_nums += norm_nums(t)
            ref_words = sorted(tl_words | img_words)
            ref_nums = sorted(set(tl_nums) | set(img_nums))
            rec = {
                "doc": doc, "page": page_no, "w": round(W, 1), "h": round(H, 1),
                "ref_tokens": ref_words,
                "ref_numbers": ref_nums,
                "n_textlayer": len(tl_words),
                "n_image_only": len(img_words - tl_words),
                "n_image_regions": len(regs),
                "reading_order": reading_order,
                "image_regions": [[round(c, 1) for c in b] for (b, _a) in regs],
            }
            json.dump(rec, open(outp, "w"))
            done += 1
            if done % 50 == 0:
                print(f"  {done}/{len(manifest)}", flush=True)
        d.close()
    print(f"done: {done} pages -> {OUT}/")


if __name__ == "__main__":
    main()
