"""
Shared loader for chunk output from the ingestion pipeline (Module 2).

Used by both the vector index build script (Session 3.2) and the
BM25 index build script (Session 3.4) — one place to change if the
chunk file location or format ever changes.
"""

import json
from pathlib import Path

CHUNKS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "ingestion" / "data" / "chunks"
)


def load_all_chunks() -> list:
    chunks = []
    for path in sorted(CHUNKS_DIR.glob("*.jsonl")):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line))
    return chunks
