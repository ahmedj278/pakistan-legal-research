"""
Main entry point for Module 2, Session 2.3 (cleaning + normalization).

Usage:
    cd ingestion/src
    python run_cleaning.py
    (Windows: py run_cleaning.py)

Deliberately separate from run_ingestion.py: this stage reads the
JSON files discovery+extraction already produced in
data/processed/<court>/, cleans the raw_text, and adds the result
back into the same file. That means you don't have to re-run the
(slower) PDF extraction step just to test or re-tune a cleaning rule
— only files with extraction_status == "ok" have text worth cleaning
in the first place; "empty_text" and "failed" files are skipped.
"""

import json
from pathlib import Path

from cleaning import clean_text
from config import OUTPUT_DIR
from logger import get_logger
from models import RawDocument


def main():
    logger = get_logger("cleaning")
    logger.info("Starting cleaning run")

    summary = {"ok": 0, "skipped": 0}
    total_chars_removed = 0

    json_files = sorted(OUTPUT_DIR.rglob("*.json"))
    if not json_files:
        logger.warning(
            f"No processed JSON files found under {OUTPUT_DIR} — "
            f"run run_ingestion.py first."
        )
        return

    for path in json_files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        doc = RawDocument(**data)

        if doc.extraction_status != "ok" or not doc.raw_text:
            doc.cleaning_status = "skipped"
            summary["skipped"] += 1
        else:
            doc.cleaned_text = clean_text(doc.raw_text)
            doc.cleaned_char_count = len(doc.cleaned_text)
            doc.cleaning_status = "ok"
            summary["ok"] += 1
            total_chars_removed += doc.char_count - doc.cleaned_char_count
            logger.info(
                f"[{doc.court}] {doc.filename}: {doc.char_count} -> "
                f"{doc.cleaned_char_count} chars"
            )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc.to_dict(), f, ensure_ascii=False, indent=2)

    logger.info(
        f"Run complete — cleaned: {summary['ok']}, skipped: {summary['skipped']}, "
        f"total chars removed: {total_chars_removed}"
    )


if __name__ == "__main__":
    main()
