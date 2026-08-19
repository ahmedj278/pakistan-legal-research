"""
Reranked hybrid retrieval (Module 4, Session 4.3).

Completes the pipeline the roadmap describes:
    BM25 + semantic search -> RRF fusion -> cross-encoder reranking

Retrieves a larger candidate pool via hybrid_search() than the final
requested n_results, then reranks that whole pool with a
cross-encoder before truncating — giving the reranker real material
to correct, not just re-sorting an already-narrow top-5 where the
right answer may already have been cut.
"""

from app.hybrid_search import hybrid_search
from app.reranker import rerank


def reranked_search(
    query_text: str,
    n_results: int = 5,
    filters: dict = None,
    model_name: str = None,
    collection_name: str = None,
    candidate_pool_size: int = 20,
) -> list:
    candidates = hybrid_search(
        query_text,
        n_results=candidate_pool_size,
        filters=filters,
        model_name=model_name,
        collection_name=collection_name,
        candidate_pool_size=candidate_pool_size,
    )
    return rerank(query_text, candidates, top_n=n_results)
