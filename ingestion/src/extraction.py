"""
Text extraction (Module 2, Session 2.2).

Takes the RawDocument objects discovery.py found and actually opens
each PDF to pull text out, page by page, using pdfplumber.

Error handling philosophy: a single bad PDF (corrupted, encrypted,
scanned-with-no-text-layer) must never crash a run over thousands of
files. Every failure is caught, logged with the filename, and the
document is marked with a status so it's still visible in the output
— not silently dropped.

Deliberately NOT doing here: OCR, cleaning/normalizing the text, or
metadata extraction. Both real samples had genuine text layers, so
OCR isn't needed yet — but if a PDF extracts almost no text, that
usually means it's an image-only page, so we flag it as
"empty_text" rather than assume it succeeded.
"""

import pdfplumber

from config import MIN_TEXT_LENGTH_THRESHOLD
from models import RawDocument


def extract_text(doc: RawDocument, logger) -> RawDocument:
    try:
        with pdfplumber.open(doc.source_path) as pdf:
            doc.page_count = len(pdf.pages)
            page_texts = [page.extract_text() or "" for page in pdf.pages]
            doc.raw_text = "\n\n".join(page_texts)
            doc.char_count = len(doc.raw_text)

        if doc.char_count < MIN_TEXT_LENGTH_THRESHOLD:
            doc.extraction_status = "empty_text"
            logger.warning(
                f"[{doc.court}] {doc.filename}: only {doc.char_count} chars extracted "
                f"— likely scanned/image-only, flagging instead of failing"
            )
        else:
            doc.extraction_status = "ok"
            logger.info(
                f"[{doc.court}] {doc.filename}: extracted {doc.char_count} chars "
                f"across {doc.page_count} page(s)"
            )

    except Exception as e:
        doc.extraction_status = "failed"
        doc.extraction_error = str(e)
        logger.error(f"[{doc.court}] {doc.filename}: extraction failed — {e}")

    return doc
