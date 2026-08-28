"""
Retrieval evaluation metrics (Module 4, Session 4.4 — brought
forward to properly compare embedding models, since manual
single-query testing on a 100-document corpus turned out too noisy
to judge quality from, especially for non-English legal terms like
"khula" that neither model was specifically trained on).

Uses document-level relevance: a result counts as a "hit" if its
source_filename is one of the query's known-relevant documents.
Simpler than exact chunk-level ground truth, and matches how a real
user judges a RAG system anyway: "did it find the right document,"
not "did it find this exact 200-character slice of it."

This module is intentionally generic — it takes a search_fn, not a
specific implementation — so the exact same evaluate() call can be
reused later for BM25, any embedding model, and eventually hybrid +
reranking (the roadmap's original plan for this session), without
rewriting the metric logic each time.
"""


def hits_at_k(results: list, relevant_filenames: set, k: int) -> bool:
    """True if any of the top-k results come from a relevant document."""
    top_k = results[:k]
    return any(r["metadata"].get("source_filename") in relevant_filenames for r in top_k)


def reciprocal_rank(results: list, relevant_filenames: set) -> float:
    """1 / rank of the first relevant result found; 0 if none found
    within the results returned."""
    for i, r in enumerate(results):
        if r["metadata"].get("source_filename") in relevant_filenames:
            return 1.0 / (i + 1)
    return 0.0


def evaluate(search_fn, test_queries: list, k_values=(1, 3, 5)) -> dict:
    """
    search_fn: callable(query_text: str, n_results: int) -> list of
    result dicts (the shape semantic_search()/keyword_search() return).

    test_queries: list of {"query": str, "relevant_filenames": [str, ...]}
    """
    max_k = max(k_values)
    per_k_hits = {k: 0 for k in k_values}
    reciprocal_ranks = []

    for item in test_queries:
        results = search_fn(item["query"], max_k)
        relevant = set(item["relevant_filenames"])

        for k in k_values:
            if hits_at_k(results, relevant, k):
                per_k_hits[k] += 1

        reciprocal_ranks.append(reciprocal_rank(results, relevant))

    n = len(test_queries)
    recall_at_k = {k: round(per_k_hits[k] / n, 3) for k in k_values}
    mrr = round(sum(reciprocal_ranks) / n, 3)

    return {"recall_at_k": recall_at_k, "mrr": mrr, "n_queries": n}


def evaluate_rag(answer_fn, test_queries: list) -> dict:
    """
    End-to-end RAG evaluation (Module 5, Session 5.6) — reuses the
    same ground-truth set and document-level-relevance reasoning as
    evaluate() above, but scores the full answer_question() output
    instead of raw retrieval.

    answer_fn: callable(query_text: str) -> dict, same shape as
    rag.answer_question()'s return (needs "citations" and "grounded").

    test_queries: list of {"query": str, "relevant_filenames": [str, ...]}

    Reports two metrics:
    - grounded_rate: fraction of answers where the LLM cited at
      least one passage (Session 5.5's `grounded` flag). Note this
      can't distinguish an honest "insufficient evidence" decline
      from an uncited hallucination — see rag.py's docstring — so a
      low grounded_rate on a set of KNOWN-ANSWERABLE queries (like
      this one) is the useful signal, not the flag alone.
    - correct_citation_rate: fraction of answers where at least one
      actual citation points to a document already known relevant
      for that query. Document-level, not exact-chunk — same
      reasoning as hits_at_k() above.

    Does not track latency or API cost — out of scope for this
    project's evaluation needs.
    """
    n = len(test_queries)
    grounded_count = 0
    correct_citation_count = 0

    for item in test_queries:
        result = answer_fn(item["query"])
        relevant = set(item["relevant_filenames"])

        if result.get("grounded"):
            grounded_count += 1

        cited_relevant = any(
            c.get("source_filename") in relevant for c in result.get("citations", [])
        )
        if cited_relevant:
            correct_citation_count += 1

    return {
        "n_queries": n,
        "grounded_rate": round(grounded_count / n, 3),
        "correct_citation_rate": round(correct_citation_count / n, 3),
    }
