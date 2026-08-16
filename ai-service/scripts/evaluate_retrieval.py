"""
Retrieval evaluation (Module 4, Session 4.4 — brought forward for
embedding model comparison, before hybrid/reranking exist).

Usage:
    cd ai-service
    python scripts/evaluate_retrieval.py
    (Windows: py scripts/evaluate_retrieval.py)

Computes Recall@1/3/5 and MRR for BM25 and every registered
embedding model, against the manually curated ground-truth queries
in eval/test_queries.json. This same script (and app/evaluation.py)
will be reused in Module 4 once hybrid fusion and reranking exist,
to run the exact same comparison across all retrieval methods —
built generically now so that part doesn't need rebuilding later.

IMPORTANT: eval/test_queries.json currently only has 2 entries
(carried over from earlier manual testing). Two data points aren't
enough to draw a real conclusion from — use
scripts/find_documents_containing.py to help find more known-answer
pairs from your own corpus and add them before trusting these
numbers. Aim for at least 5-10.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.bm25_search import keyword_search  # noqa: E402
from app.evaluation import evaluate  # noqa: E402
from app.model_registry import EMBEDDING_MODELS  # noqa: E402
from app.search import semantic_search  # noqa: E402

TEST_QUERIES_PATH = Path(__file__).resolve().parent.parent / "eval" / "test_queries.json"


def main():
    if not TEST_QUERIES_PATH.exists():
        print(f"No test set found at {TEST_QUERIES_PATH}")
        return

    with open(TEST_QUERIES_PATH, "r", encoding="utf-8") as f:
        test_queries = json.load(f)

    if len(test_queries) < 5:
        print(
            f"WARNING: only {len(test_queries)} test queries — results below "
            f"will be noisy. Run scripts/find_documents_containing.py to find "
            f"more known-answer pairs and add them to eval/test_queries.json. "
            f"Recommend at least 5-10 for a meaningful MRR average.\n"
        )

    print(f"Evaluating against {len(test_queries)} test queries\n")

    results_table = []

    bm25_metrics = evaluate(lambda q, n: keyword_search(q, n_results=n), test_queries)
    results_table.append(("bm25", bm25_metrics))

    for model_key, model_config in EMBEDDING_MODELS.items():
        def search_fn(q, n, model_config=model_config):
            return semantic_search(
                q,
                n_results=n,
                model_name=model_config["model_name"],
                collection_name=model_config["collection_name"],
            )

        metrics = evaluate(search_fn, test_queries)
        results_table.append((model_key, metrics))

    print(f"{'Method':<12} {'Recall@1':<10} {'Recall@3':<10} {'Recall@5':<10} {'MRR':<8}")
    print("-" * 52)
    for name, m in results_table:
        r = m["recall_at_k"]
        print(
            f"{name:<12} {r.get(1, '-'):<10} {r.get(3, '-'):<10} "
            f"{r.get(5, '-'):<10} {m['mrr']:<8}"
        )


if __name__ == "__main__":
    main()
