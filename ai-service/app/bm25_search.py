"""
BM25 keyword search (Module 3, Session 3.4).

Complements semantic search (Session 3.3): BM25 finds documents
containing the literal query words, weighted by term rarity, rather
than by meaning. This is what reliably finds a specific term (a case
number, a specific legal term like "khula") even when no
semantically-similar-but-differently-worded match exists — the exact
gap identified during manual testing of semantic search alone (see
docs/retrieval-notes.md).

Uses rank_bm25 (BM25Okapi) — a small, pure-Python implementation, no
C extension to compile (unlike chromadb's hnswlib dependency). No
separate server; the index is built once from chunk output and
persisted to disk with pickle, so it doesn't need rebuilding on
every server restart.
"""

import pickle
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.config import settings

BM25_INDEX_PATH = Path(settings.chroma_persist_dir).parent / "bm25_index.pkl"

_bm25 = None
_chunk_records = None


def tokenize(text: str) -> list:
    # Simple, consistent tokenizer: lowercase, split on word
    # boundaries. Doesn't need to match the embedding model's
    # tokenizer at all — BM25 works from its own token statistics.
    return re.findall(r"\w+", text.lower())


def build_index(chunks: list):
    """Builds a BM25 index from a list of chunk dicts (as produced
    by Module 2) and persists it to disk."""
    global _bm25, _chunk_records

    tokenized_corpus = [tokenize(c["text"]) for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)

    BM25_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BM25_INDEX_PATH, "wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)

    _bm25 = bm25
    _chunk_records = chunks


def _load_index():
    global _bm25, _chunk_records
    if _bm25 is not None:
        return
    if not BM25_INDEX_PATH.exists():
        raise FileNotFoundError(
            f"BM25 index not found at {BM25_INDEX_PATH} — run "
            f"scripts/build_bm25_index.py first."
        )
    with open(BM25_INDEX_PATH, "rb") as f:
        data = pickle.load(f)
    _bm25 = data["bm25"]
    _chunk_records = data["chunks"]


def keyword_search(query_text: str, n_results: int = 5) -> list:
    _load_index()

    tokenized_query = tokenize(query_text)
    scores = _bm25.get_scores(tokenized_query)

    ranked = sorted(
        zip(_chunk_records, scores), key=lambda pair: pair[1], reverse=True
    )[:n_results]

    results = []
    for chunk, score in ranked:
        results.append(
            {
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "metadata": {k: v for k, v in chunk.items() if k != "text"},
                "bm25_score": round(float(score), 4),
            }
        )
    return results
