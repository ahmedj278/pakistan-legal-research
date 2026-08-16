"""
Helper for building the evaluation test set (eval/test_queries.json).

Usage:
    cd ai-service
    python scripts/find_documents_containing.py khula
    (Windows: py scripts/find_documents_containing.py khula)

Searches the actual chunk text (the same data search uses) for a
literal term and lists which source documents contain it — so you
can confirm the correct filename for a test_queries.json entry
without manually opening PDFs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunk_loader import load_all_chunks  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/find_documents_containing.py <term>")
        return
    term = sys.argv[1].lower()

    chunks = load_all_chunks()
    seen = {}
    for c in chunks:
        if term in c["text"].lower():
            fname = c["source_filename"]
            if fname not in seen:
                seen[fname] = {
                    "case_title": c.get("case_title"),
                    "court": c.get("court"),
                    "count": 0,
                }
            seen[fname]["count"] += 1

    if not seen:
        print(f'No chunks contain "{term}"')
        return

    print(f'Documents containing "{term}":\n')
    for fname, info in sorted(seen.items(), key=lambda x: -x[1]["count"]):
        print(f"  {fname}  ({info['count']} matching chunk(s))")
        print(f"    court: {info['court']}, title: {info['case_title']}")
        print()


if __name__ == "__main__":
    main()
