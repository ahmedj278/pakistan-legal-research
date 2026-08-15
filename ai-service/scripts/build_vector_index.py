"""
Builds the vector index(es) from chunk output (Module 3, Session
3.2; extended for multi-model comparison).

Usage:
    cd ai-service
    python scripts/build_vector_index.py            # builds ALL registered models
    python scripts/build_vector_index.py minilm      # builds just one
    (Windows: py scripts/build_vector_index.py)

Reads every *.jsonl file in ingestion/data/chunks/ (produced by
Module 2), and for each embedding model registered in
app/model_registry.py, embeds every chunk with that model and stores
it in that model's own ChromaDB collection. Safe to re-run — uses
upsert, so running it again after re-processing PDFs updates
existing entries by chunk_id rather than duplicating them.

Building "all" models sequentially in one run is deliberate for this
project's scale (~100 sample documents): simpler than juggling
separate commands per model, and still finishes in a few minutes.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunk_loader import load_all_chunks  # noqa: E402
from app.embeddings import embed_texts  # noqa: E402
from app.model_registry import EMBEDDING_MODELS  # noqa: E402
from app.vector_store import add_chunks, count  # noqa: E402

BATCH_SIZE = 32


def build_for_model(chunks: list, model_key: str, model_config: dict):
    model_name = model_config["model_name"]
    collection_name = model_config["collection_name"]

    print(f"\n=== {model_key} ({model_name}) -> collection '{collection_name}' ===")
    start = time.time()

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        ids = [c["chunk_id"] for c in batch]
        metadatas = [{k: v for k, v in c.items() if k != "text"} for c in batch]

        embeddings = embed_texts(texts, model_name=model_name)
        add_chunks(
            chunk_ids=ids,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            collection_name=collection_name,
        )
        print(f"  embedded {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)} chunks")

    elapsed = time.time() - start
    total = count(collection_name=collection_name)
    print(f"Done in {elapsed:.1f}s — '{collection_name}' now has {total} chunks")


def main():
    chunks = load_all_chunks()
    if not chunks:
        print("No chunk files found — run the Module 2 pipeline first.")
        return

    print(f"Found {len(chunks)} chunks")

    requested = sys.argv[1] if len(sys.argv) > 1 else None
    if requested:
        if requested not in EMBEDDING_MODELS:
            print(f"Unknown model key '{requested}'. Options: {list(EMBEDDING_MODELS)}")
            return
        models_to_build = {requested: EMBEDDING_MODELS[requested]}
    else:
        models_to_build = EMBEDDING_MODELS

    for model_key, model_config in models_to_build.items():
        build_for_model(chunks, model_key, model_config)


if __name__ == "__main__":
    main()
