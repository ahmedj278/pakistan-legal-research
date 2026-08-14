"""
Metadata filtering (Module 3, Session 3.5).

Shared between semantic search (which needs a ChromaDB-shaped
"where" clause) and BM25 search (which just filters a Python list),
so both search methods support the same filter fields the same way.
"""


def build_filters(court: str = None, year: int = None, document_type: str = None) -> dict:
    filters = {}
    if court:
        filters["court"] = court
    if year:
        filters["year"] = year
    if document_type:
        filters["document_type"] = document_type
    return filters


def matches_filters(metadata: dict, filters: dict) -> bool:
    """Used by BM25 search, which filters a plain Python list."""
    return all(metadata.get(key) == value for key, value in filters.items())


def to_chroma_where(filters: dict):
    """
    Converts a plain {field: value} dict into ChromaDB's expected
    "where" clause shape. A single filter is just {field: value};
    ChromaDB requires an explicit "$and" wrapper for more than one.
    Returns None for no filters, since Chroma expects the "where"
    argument to be omitted entirely rather than an empty dict.
    """
    if not filters:
        return None
    if len(filters) == 1:
        key, value = next(iter(filters.items()))
        return {key: value}
    return {"$and": [{k: v} for k, v in filters.items()]}
