"""
Builds the BM25 keyword index from chunk output (Module 3, Session 3.4).

Usage:
    cd ai-service
    python scripts/build_bm25_index.py
    (Windows: py scripts/build_bm25_index.py)

Much faster than building the vector index — no embedding model, no
CPU-heavy encoding, just tokenizing and counting term frequencies.
Always rebuilds from scratch when re-run — BM25 needs corpus-wide
term statistics, so there's no meaningful "upsert" the way there is
for the vector store.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.bm25_search import BM25_INDEX_PATH, build_index  # noqa: E402
from app.chunk_loader import load_all_chunks  # noqa: E402


def main():
    chunks = load_all_chunks()
    if not chunks:
        print("No chunk files found — run the Module 2 pipeline first.")
        return

    print(f"Building BM25 index from {len(chunks)} chunks...")
    start = time.time()
    build_index(chunks)
    elapsed = time.time() - start

    print(f"Done in {elapsed:.1f}s — index saved to {BM25_INDEX_PATH}")


if __name__ == "__main__":
    main()
