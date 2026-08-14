"""
Standalone script to test embedding generation end-to-end against
real chunk output from the ingestion pipeline (Module 2).

Usage:
    cd ai-service
    python scripts/test_embeddings.py
    (Windows: py scripts/test_embeddings.py)

Not part of the FastAPI app — this is a one-off sanity check to run
after `pip install -r requirements.txt`, before wiring embeddings
into the vector database (Session 3.2). Confirms two things:
1. The model loads and produces vectors of the expected dimension.
2. The vectors are actually semantically meaningful — two chunks
   from the SAME judgment should be more similar to each other than
   a chunk from a completely different, unrelated judgment.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.embeddings import embed_texts, embedding_dimension  # noqa: E402

CHUNKS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "ingestion" / "data" / "chunks"
)


def load_chunks(court: str, limit: int = 3) -> list:
    path = CHUNKS_DIR / f"{court}.jsonl"
    if not path.exists():
        return []
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
            if len(chunks) >= limit:
                break
    return chunks


def cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b)


def main():
    print(f"Embedding model dimension: {embedding_dimension()}")

    sc_chunks = load_chunks("supreme_court", limit=2)
    ihc_chunks = load_chunks("islamabad_high_court", limit=1)

    if len(sc_chunks) < 2:
        print(
            "Need at least 2 Supreme Court chunks to run this test — "
            "run the Module 2 ingestion pipeline first."
        )
        return

    texts = [c["text"] for c in sc_chunks] + [c["text"] for c in ihc_chunks]
    vectors = embed_texts(texts)

    print(f"Embedded {len(vectors)} chunks, each with {len(vectors[0])} dimensions")

    same_doc_similarity = cosine_similarity(vectors[0], vectors[1])
    print(
        f"\nSimilarity between 2 chunks from the SAME SC judgment: "
        f"{same_doc_similarity:.3f}"
    )

    if ihc_chunks:
        diff_doc_similarity = cosine_similarity(vectors[0], vectors[2])
        print(
            f"Similarity between an SC chunk and an unrelated IHC chunk: "
            f"{diff_doc_similarity:.3f}"
        )
        if same_doc_similarity > diff_doc_similarity:
            print("\nPASS - same-document chunks are more similar than unrelated ones")
        else:
            print("\nUNEXPECTED - unrelated chunks scored higher; worth a second look")


if __name__ == "__main__":
    main()
