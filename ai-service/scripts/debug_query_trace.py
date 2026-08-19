"""
Diagnostic: traces a single query through the retrieval pipeline
step by step, to determine whether a specific expected chunk was
actually in the pre-rerank candidate pool — answers "is this a
retrieval problem or a reranking problem" directly, with evidence,
instead of guessing.

Usage:
    cd ai-service
    python scripts/debug_query_trace.py "PLD 2024 SC 1276" "c.a._106_k_2024.pdf::chunk_3"
    (Windows: py scripts/debug_query_trace.py "PLD 2024 SC 1276" "c.a._106_k_2024.pdf::chunk_3")
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.hybrid_search import hybrid_search  # noqa: E402
from app.reranker import rerank  # noqa: E402

CANDIDATE_POOL_SIZE = 20


def main():
    if len(sys.argv) < 3:
        print('Usage: python scripts/debug_query_trace.py "<query>" "<expected_chunk_id>"')
        return

    query = sys.argv[1]
    expected_id = sys.argv[2]

    print(f'Query: "{query}"')
    print(f"Looking for: {expected_id}\n")

    # Step 1: was it even retrieved by hybrid (BM25 + semantic + RRF),
    # BEFORE reranking touches anything?
    candidates = hybrid_search(
        query, n_results=CANDIDATE_POOL_SIZE, candidate_pool_size=CANDIDATE_POOL_SIZE
    )
    print(f"Hybrid candidate pool size: {len(candidates)}")

    match = next((c for c in candidates if c["chunk_id"] == expected_id), None)
    if not match:
        print(f"\nNOT FOUND in the hybrid candidate pool (checked top {CANDIDATE_POOL_SIZE}).")
        print("This is a RETRIEVAL problem, not a reranking problem —")
        print("the reranker never had a chance to see this chunk at all.")
        return

    rank = candidates.index(match) + 1
    print(f"FOUND in hybrid pool at rank {rank}/{len(candidates)}, rrf_score={match['rrf_score']}")

    # Step 2: given that it WAS in the pool, where does reranking put it?
    print("\nReranking the same candidate pool...")
    reranked = rerank(query, candidates)
    rerank_match = next((c for c in reranked if c["chunk_id"] == expected_id), None)
    rerank_rank = reranked.index(rerank_match) + 1

    print(
        f"After reranking: rank {rerank_rank}/{len(reranked)}, "
        f"rerank_score={rerank_match['rerank_score']}"
    )
    print("\nTop 5 after reranking:")
    for i, r in enumerate(reranked[:5], 1):
        marker = "  <-- expected chunk" if r["chunk_id"] == expected_id else ""
        print(f"  {i}. {r['chunk_id']}  rerank_score={r['rerank_score']}{marker}")

    if rerank_rank <= 5:
        print("\nReranking correctly promoted it into the top 5.")
    elif rerank_rank < rank:
        print(
            f"\nReranking IMPROVED its rank ({rank} -> {rerank_rank}) but not enough "
            f"to reach the top 5. The reranker model itself may be under-scoring it "
            f"relative to other candidates — worth inspecting the actual scores above."
        )
    else:
        print(
            f"\nReranking did NOT improve its rank ({rank} -> {rerank_rank}). "
            f"This points at the reranker model itself, not retrieval — "
            f"cross-encoder/ms-marco-MiniLM-L-6-v2 is a general-purpose model, "
            f"not tuned for exact citation-string matching."
        )


if __name__ == "__main__":
    main()
