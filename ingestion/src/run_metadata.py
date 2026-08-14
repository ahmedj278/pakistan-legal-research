"""
Main entry point for Module 2, Session 2.4 (metadata extraction).

Usage:
    cd ingestion/src
    python run_metadata.py
    (Windows: py run_metadata.py)

Reads the JSON files run_cleaning.py already produced, extracts
metadata from the cleaned text, and writes the fields back into the
same file.
"""

import json

from config import OUTPUT_DIR
from logger import get_logger
from metadata import extract_metadata
from models import RawDocument


def main():
    logger = get_logger("metadata")
    logger.info("Starting metadata extraction run")

    summary = {"ok": 0, "partial": 0, "skipped": 0}

    json_files = sorted(OUTPUT_DIR.rglob("*.json"))
    if not json_files:
        logger.warning(f"No processed JSON files found under {OUTPUT_DIR}")
        return

    for path in json_files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        doc = RawDocument(**data)

        if doc.cleaning_status != "ok":
            doc.metadata_status = "skipped"
        else:
            doc = extract_metadata(doc, logger)

        summary[doc.metadata_status] = summary.get(doc.metadata_status, 0) + 1

        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc.to_dict(), f, ensure_ascii=False, indent=2)

    logger.info(
        f"Run complete — ok: {summary['ok']}, partial: {summary['partial']}, "
        f"skipped: {summary['skipped']}"
    )


if __name__ == "__main__":
    main()
