"""
Builds the vector index from chunk output (Module 3, Session 3.2).

Usage:
    cd ai-service
    python scripts/build_vector_index.py
    (Windows: py scripts/build_vector_index.py)

Reads every *.jsonl file in ingestion/data/chunks/ (produced by
Module 2), embeds each chunk's text in batches, and stores it in
ChromaDB along with its metadata. Safe to re-run — uses upsert, so
running it again after re-processing PDFs updates existing entries
by chunk_id rather than duplicating them.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunk_loader import load_all_chunks  # noqa: E402
from app.embeddings import embed_texts  # noqa: E402
from app.vector_store import add_chunks, count  # noqa: E402

CHUNKS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "ingestion" / "data" / "chunks"
)
BATCH_SIZE = 32


def main():
    chunks = load_all_chunks()
    if not chunks:
        print(f"No chunk files found in {CHUNKS_DIR} — run the Module 2 pipeline first.")
        return

    court_files = list(CHUNKS_DIR.glob("*.jsonl"))
    print(f"Found {len(chunks)} chunks across {len(court_files)} court file(s)")

    start = time.time()
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        ids = [c["chunk_id"] for c in batch]
        metadatas = [{k: v for k, v in c.items() if k != "text"} for c in batch]

        embeddings = embed_texts(texts)
        add_chunks(chunk_ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)

        print(f"  embedded {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)} chunks")

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s — collection now has {count()} total chunks")


if __name__ == "__main__":
    main()
