"""
Cross-encoder reranking (Module 4, Session 4.3).

Unlike RRF fusion (Sessions 4.1-4.2), which only combines RANK
POSITIONS from independent retrievers, a cross-encoder reads the
query and each candidate passage TOGETHER and produces a direct
relevance judgment for that specific pair. This targets the exact
failure found in manual testing (docs/retrieval-notes.md, Test 8):
a citation-lookup query where the literally-correct chunk was buried
by RRF beneath chunks that only superficially resembled a citation
list. A cross-encoder can, in principle, recognize that the correct
chunk explicitly contains the exact queried citation string,
regardless of where RRF happened to rank it.

Uses sentence-transformers' CrossEncoder — already a dependency
(same package as the embedding models), no new install needed — with
a standard, general-purpose reranker model. Not legal-domain-tuned;
a real limitation worth documenting, same situation as the embedding
model comparison, but swappable later via RERANKER_MODEL_NAME alone.
"""

from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.config import settings


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    return CrossEncoder(settings.reranker_model_name)


def rerank(query_text: str, candidates: list, top_n: int = None) -> list:
    """
    candidates: list of result dicts, each with a "text" key.
    Returns the same dicts with an added "rerank_score", sorted by
    that score descending. Truncates to top_n if given.
    """
    if not candidates:
        return []

    model = get_reranker()
    pairs = [(query_text, c["text"]) for c in candidates]
    scores = model.predict(pairs)

    scored = list(zip(candidates, scores))
    scored.sort(key=lambda pair: pair[1], reverse=True)

    results = []
    for candidate, score in scored:
        record = dict(candidate)
        record["rerank_score"] = round(float(score), 5)
        results.append(record)

    return results[:top_n] if top_n else results
