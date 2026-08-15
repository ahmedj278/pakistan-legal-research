"""
Compares embedding models side by side on the same queries (Module
3 follow-up).

Usage:
    cd ai-service
    python scripts/compare_embedding_models.py
    python scripts/compare_embedding_models.py "your custom query"
    (Windows: py scripts/compare_embedding_models.py)

Runs each registered model's collection (app/model_registry.py)
against the same set of queries and prints results side by side, so
differences are directly visible rather than requiring separate
manual runs to be compared by eye. Defaults to the three queries
already used for manual testing (see docs/retrieval-notes.md) —
"khula" is the most interesting one, since it's the query where
MiniLM was already observed to miss the right document.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.model_registry import EMBEDDING_MODELS  # noqa: E402
from app.search import semantic_search  # noqa: E402

DEFAULT_QUERIES = [
    "khula",
    "murder",
    "police promotion seniority dispute",
]


def run_comparison(query_text: str, n_results: int = 3):
    print(f"\n{'=' * 70}")
    print(f"QUERY: \"{query_text}\"")
    print("=" * 70)

    for model_key, model_config in EMBEDDING_MODELS.items():
        print(f"\n--- {model_key} ({model_config['description']}) ---")
        try:
            results = semantic_search(
                query_text,
                n_results=n_results,
                model_name=model_config["model_name"],
                collection_name=model_config["collection_name"],
            )
        except Exception as e:
            print(f"  ERROR: {e}")
            print(f"  (has scripts/build_vector_index.py been run for this model?)")
            continue

        if not results:
            print("  (no results — has the index been built for this model?)")
            continue

        for r in results:
            meta = r["metadata"]
            title = meta.get("case_title") or meta.get("source_filename", "?")
            print(f"  [{r['similarity']:.3f}] {meta.get('court', '?'):22s} {title[:70]}")


def main():
    queries = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_QUERIES
    for query_text in queries:
        run_comparison(query_text)


if __name__ == "__main__":
    main()
