"""
Main entry point for Module 2, Sessions 2.1–2.2 (discovery + extraction).

Usage:
    cd ingestion/src
    python run_ingestion.py
    (Windows: py run_ingestion.py)

For each court configured in config.SOURCE_DIRS:
  1. Discover PDFs in its source directory.
  2. Extract text from each one.
  3. Write one JSON file per PDF to data/processed/<court>/.
  4. Print a summary of ok / empty_text / failed counts.

Nothing here does cleaning, metadata extraction, or chunking yet —
those are later sessions. This stage's only job is: turn PDFs on
disk into raw extracted text on disk, reliably.
"""

import json

from config import SOURCE_DIRS, OUTPUT_DIR
from discovery import discover_pdfs
from extraction import extract_text
from logger import get_logger


def main():
    logger = get_logger("ingestion")
    logger.info("Starting ingestion run (discovery + extraction)")

    summary = {"ok": 0, "empty_text": 0, "failed": 0}

    for court, directory in SOURCE_DIRS.items():
        court_output_dir = OUTPUT_DIR / court
        court_output_dir.mkdir(parents=True, exist_ok=True)

        documents = discover_pdfs(directory, court, logger)

        for doc in documents:
            doc = extract_text(doc, logger)
            summary[doc.extraction_status] = summary.get(doc.extraction_status, 0) + 1

            output_path = court_output_dir / f"{doc.filename}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(doc.to_dict(), f, ensure_ascii=False, indent=2)

    logger.info(
        f"Run complete — ok: {summary['ok']}, "
        f"empty_text: {summary['empty_text']}, failed: {summary['failed']}"
    )


if __name__ == "__main__":
    main()
