"""
Document retrieval (Module 7 prerequisite).

Search results (Modules 3-4) only carry chunk-sized text — enough to
show a relevant excerpt, not the full judgment. The Judgment Viewer
page (Session 7.4) needs the complete document text, which lives in
the processed-document JSON files the ingestion pipeline already
writes to ingestion/data/processed/<court>/<filename>.json (see
ingestion/src/*.py) — this module reads that, rather than storing
full text a second time somewhere else.

Court subdirectories are discovered dynamically (not a hardcoded
list) so this doesn't silently go stale if another court is added
later without a matching code change here.
"""

import json
from pathlib import Path

from app.config import AI_SERVICE_DIR

# ai-service/ -> repo root -> ingestion/data/processed
PROCESSED_DATA_DIR = AI_SERVICE_DIR.parent / "ingestion" / "data" / "processed"


def get_document(filename: str, court: str = None) -> dict:
    """
    Returns {"filename", "court", "metadata": {...}, "text": "..."}
    for one processed judgment, or None if not found.

    filename: the source PDF filename exactly as it appears in a
    chunk's metadata.source_filename (e.g. "c.a._106_k_2024.pdf") —
    not a filesystem path.

    court: optional court slug (e.g. "supreme_court") — pass this
    when already known (e.g. from a search result's metadata) to
    look directly in that folder instead of scanning every court
    subdirectory.
    """
    if not PROCESSED_DATA_DIR.exists():
        return None

    if court:
        court_dirs = [PROCESSED_DATA_DIR / court]
    else:
        court_dirs = [d for d in PROCESSED_DATA_DIR.iterdir() if d.is_dir()]

    for court_dir in court_dirs:
        json_path = court_dir / f"{filename}.json"
        if not json_path.exists():
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "filename": data.get("filename"),
            "court": data.get("court"),
            "metadata": {
                "court_name": data.get("court_name"),
                "case_title": data.get("case_title"),
                "case_number": data.get("case_number"),
                "year": data.get("year"),
                "judges": data.get("judges"),
                "document_type": data.get("document_type"),
                "citation": data.get("citation"),
                "hearing_date": data.get("hearing_date"),
                "decision_date": data.get("decision_date"),
            },
            # cleaned_text is what was actually chunked/indexed for
            # search — prefer it over raw_text, which may still carry
            # OCR noise or page headers the cleaning step strips.
            "text": data.get("cleaned_text") or data.get("raw_text") or "",
        }

    return None
