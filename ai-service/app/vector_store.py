"""
Vector database integration (Module 3, Session 3.2).

Wraps ChromaDB behind a small interface, same reasoning as
embeddings.py: retrieval code should depend on this module's
functions, not on ChromaDB directly, so the vector database could be
swapped for something else later without rewriting every caller.

ChromaDB specifically (the project's planned default): needs no
separate server process — it persists straight to a local folder,
which keeps local development simple. That folder
(settings.chroma_persist_dir) is gitignored, same as any other
generated data.
"""

import chromadb
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
from app.config import settings

_client = None
_collection = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def sanitize_metadata(meta: dict) -> dict:
    """
    ChromaDB metadata values must be str, int, float, or bool — no
    None and no lists. This converts a chunk's metadata dict into a
    Chroma-safe version: fields that are None are dropped entirely
    (Chroma rejects None outright), and list fields (like `judges`)
    are joined into a single comma-separated string.
    """
    safe = {}
    for key, value in meta.items():
        if value is None:
            continue
        if isinstance(value, list):
            safe[key] = ", ".join(str(v) for v in value)
        else:
            safe[key] = value
    return safe


def add_chunks(chunk_ids: list, texts: list, embeddings: list, metadatas: list):
    collection = get_collection()
    safe_metadatas = [sanitize_metadata(m) for m in metadatas]
    collection.upsert(
        ids=chunk_ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=safe_metadatas,
    )


def query(query_embedding: list, n_results: int = 5, where: dict = None) -> dict:
    collection = get_collection()
    kwargs = {"query_embeddings": [query_embedding], "n_results": n_results}
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


def count() -> int:
    return get_collection().count()
