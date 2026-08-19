"""
Hybrid retrieval via Reciprocal Rank Fusion (Module 4, Sessions 4.1-4.2).

Combines BM25 (keyword_search) and semantic search (semantic_search)
results into one ranked list using Reciprocal Rank Fusion (RRF).

Why RRF instead of averaging raw scores: a BM25 score and a cosine
similarity score are not on the same scale and don't mean the same
thing — a BM25 score of 5 has no defined relationship to a
similarity of 0.5, so averaging them directly would be arbitrary.
RRF sidesteps this entirely by only looking at each result's RANK
POSITION within each list, never its raw score. Standard, simple,
robust technique from IR literature (Cormack et al., 2009) — exactly
what the project roadmap specifies for this session.

Formula: for each unique result appearing in either list,
    rrf_score = sum, over every list containing it, of 1 / (k + rank)
where rank is the 1-indexed position in that list, and k=60 is the
standard smoothing constant from the original paper — large enough
that a #1-vs-#2 rank difference doesn't dominate the total
disproportionately.
"""

from app.bm25_search import keyword_search
from app.search import semantic_search

RRF_K = 60


def reciprocal_rank_fusion(*ranked_lists, k: int = RRF_K) -> list:
    """
    Takes any number of ranked result lists (each a list of result
    dicts with a "chunk_id" key, ordered best-to-worst), and returns
    one fused list ordered by combined RRF score, descending.
    """
    scores = {}
    chunk_lookup = {}

    for ranked_list in ranked_lists:
        for rank, result in enumerate(ranked_list, start=1):
            chunk_id = result["chunk_id"]
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
            # Keep the first-seen full record for this chunk_id, so
            # its text/metadata is still available in the output.
            if chunk_id not in chunk_lookup:
                chunk_lookup[chunk_id] = result

    fused = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)

    results = []
    for chunk_id, rrf_score in fused:
        record = dict(chunk_lookup[chunk_id])
        record["rrf_score"] = round(rrf_score, 5)
        results.append(record)

    return results


def hybrid_search(
    query_text: str,
    n_results: int = 5,
    filters: dict = None,
    candidate_pool_size: int = 20,
    model_name: str = None,
    collection_name: str = None,
) -> list:
    """
    Runs BM25 and semantic search with a larger candidate pool than
    n_results (so fusion has real material to combine, not just each
    method's already-truncated top N), fuses with RRF, returns the
    top n_results.

    model_name/collection_name select which embedding model backs
    the semantic half — defaults to settings.embedding_model_name if
    not given (same default semantic_search() itself uses).
    """
    bm25_results = keyword_search(query_text, n_results=candidate_pool_size, filters=filters)
    semantic_results = semantic_search(
        query_text,
        n_results=candidate_pool_size,
        filters=filters,
        model_name=model_name,
        collection_name=collection_name,
    )

    fused = reciprocal_rank_fusion(bm25_results, semantic_results)
    return fused[:n_results]
