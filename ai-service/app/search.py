"""
Basic semantic search (Module 3, Session 3.3).

Given a natural-language query, embeds it with the same model used
for the chunks, and finds the most similar chunks already stored in
the vector store. This is dense/semantic retrieval only — no
keyword search (BM25), fusion, or reranking yet; those are Module 4.
"""

from app.embeddings import embed_texts
from app.vector_store import query as vector_query


def semantic_search(query_text: str, n_results: int = 5, where: dict = None) -> list:
    query_embedding = embed_texts([query_text])[0]
    results = vector_query(query_embedding, n_results=n_results, where=where)

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    formatted = []
    for i in range(len(ids)):
        formatted.append(
            {
                "chunk_id": ids[i],
                "text": documents[i],
                "metadata": metadatas[i],
                # Chroma returns cosine DISTANCE (lower = more similar).
                # Converted to a similarity score (higher = more
                # similar) since that reads more intuitively.
                "similarity": round(1 - distances[i], 4),
            }
        )

    return formatted
