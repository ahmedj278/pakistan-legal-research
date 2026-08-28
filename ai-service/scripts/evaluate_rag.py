"""
End-to-end RAG evaluation (Module 5, Session 5.6).

Usage:
    cd ai-service
    python scripts/evaluate_rag.py
    (Windows: py scripts/evaluate_rag.py)

Runs the full answer_question() pipeline (retrieval -> rerank -> LLM
-> citations -> grounded flag) against the same ground-truth queries
used for retrieval-only evaluation (eval/test_queries.json), and
reports:

- grounded_rate: fraction of answers where the LLM cited at least
  one passage. Since every query in this set is known-answerable
  from the corpus, a low grounded_rate here is a real signal (the
  LLM is under-citing), not an expected "insufficient evidence" case.
- correct_citation_rate: fraction of answers where at least one
  actual citation points to a document already known relevant for
  that query (document-level, not exact-chunk — see
  app/evaluation.py for the reasoning).

IMPORTANT: this makes one real LLM API call per test query — not
free-tier-safe to run in a loop or CI on every change. Run it
intentionally when you want a real signal, not automatically.

Same caveat as evaluate_retrieval.py: eval/test_queries.json needs
enough entries (5-10+) for these rates to mean anything; check its
current size before trusting a single run's numbers.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rag import answer_question  # noqa: E402
from app.evaluation import evaluate_rag  # noqa: E402

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
            f"will be noisy. See scripts/evaluate_retrieval.py's same warning; "
            f"this reuses the identical test set.\n"
        )

    print(f"Running end-to-end RAG evaluation against {len(test_queries)} test queries")
    print("(this makes one real LLM API call per query)\n")

    metrics = evaluate_rag(lambda q: answer_question(q, n_passages=5), test_queries)

    print(f"{'Metric':<24} {'Value'}")
    print("-" * 36)
    print(f"{'grounded_rate':<24} {metrics['grounded_rate']}")
    print(f"{'correct_citation_rate':<24} {metrics['correct_citation_rate']}")
    print(f"{'n_queries':<24} {metrics['n_queries']}")


if __name__ == "__main__":
    main()
