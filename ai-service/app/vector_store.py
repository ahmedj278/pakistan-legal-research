"""
Vector database integration (Module 3, Session 3.2; extended for
multi-model comparison).

Wraps ChromaDB behind a small interface, same reasoning as
embeddings.py: retrieval code should depend on this module's
functions, not on ChromaDB directly, so the vector database could be
swapped for something else later without rewriting every caller.

ChromaDB specifically (the project's planned default): needs no
separate server process — it persists straight to a local folder,
which keeps local development simple. That folder
(settings.chroma_persist_dir) is gitignored, same as any other
generated data.

Every function accepts an optional `collection_name` override,
defaulting to `settings.chroma_collection_name`. This is what allows
one ChromaDB store to hold a separate collection per embedding model
(see app/model_registry.py) — vectors from different models are not
comparable, so they must never share a collection.
"""

import chromadb

from app.config import settings

_client = None
_collections = {}


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def get_collection(collection_name: str = None):
    collection_name = collection_name or settings.chroma_collection_name
    if collection_name not in _collections:
        client = get_client()
        _collections[collection_name] = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
    return _collections[collection_name]


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


def add_chunks(
    chunk_ids: list,
    texts: list,
    embeddings: list,
    metadatas: list,
    collection_name: str = None,
):
    collection = get_collection(collection_name)
    safe_metadatas = [sanitize_metadata(m) for m in metadatas]
    collection.upsert(
        ids=chunk_ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=safe_metadatas,
    )


def query(
    query_embedding: list,
    n_results: int = 5,
    where: dict = None,
    collection_name: str = None,
) -> dict:
    collection = get_collection(collection_name)
    kwargs = {"query_embeddings": [query_embedding], "n_results": n_results}
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


def count(collection_name: str = None) -> int:
    return get_collection(collection_name).count()
