"""
FastAPI entry point for the AI service.

Health check (Module 1), semantic search, BM25 keyword search,
metadata filtering (Module 3), hybrid retrieval + reranking
(Module 4), RAG (Module 5), and query preprocessing + expansion
(Module 6, Sessions 6.1-6.2).

Query preprocessing (6.1, free/instant) is applied here, at the API
boundary, to every incoming query on every endpoint below — this is
the one place raw user text actually enters the system, so it's the
right place to clean it once rather than duplicating the call inside
every individual search function.

Query expansion (6.2, costs one extra LLM call) is intentionally NOT
applied automatically to /search or /ask — it's exposed as its own
opt-in endpoint, /search/expanded, so it doesn't silently double API
quota usage on every request.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.search import semantic_search
from app.bm25_search import keyword_search
from app.hybrid_search import hybrid_search
from app.reranked_search import reranked_search
from app.rag import answer_question
from app.filters import build_filters
from app.query_processing import preprocess_query, multi_query_search
from app.documents import get_document

app = FastAPI(
    title="Pakistan Legal Research - AI Service",
    description="Handles document processing, retrieval, and RAG.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class SearchRequest(BaseModel):
    query: str
    n_results: int = 5
    # Optional metadata filters (Session 3.5). court expects the
    # internal slug ("supreme_court" / "islamabad_high_court"), not
    # the display name.
    court: Optional[str] = None
    year: Optional[int] = None
    document_type: Optional[str] = None


@app.post("/search")
def search(req: SearchRequest):
    query = preprocess_query(req.query)
    filters = build_filters(req.court, req.year, req.document_type)
    results = semantic_search(query, n_results=req.n_results, filters=filters)
    return {"query": query, "filters": filters, "results": results}


@app.post("/search/keyword")
def search_keyword(req: SearchRequest):
    query = preprocess_query(req.query)
    filters = build_filters(req.court, req.year, req.document_type)
    results = keyword_search(query, n_results=req.n_results, filters=filters)
    return {"query": query, "filters": filters, "results": results}


@app.post("/search/hybrid")
def search_hybrid(req: SearchRequest):
    query = preprocess_query(req.query)
    filters = build_filters(req.court, req.year, req.document_type)
    results = hybrid_search(query, n_results=req.n_results, filters=filters)
    return {"query": query, "filters": filters, "results": results}


@app.post("/search/reranked")
def search_reranked(req: SearchRequest):
    query = preprocess_query(req.query)
    filters = build_filters(req.court, req.year, req.document_type)
    results = reranked_search(query, n_results=req.n_results, filters=filters)
    return {"query": query, "filters": filters, "results": results}


class ExpandedSearchRequest(SearchRequest):
    n_variants: int = 3


@app.post("/search/expanded")
def search_expanded(req: ExpandedSearchRequest):
    """
    Session 6.2 — retrieves using the original query plus n_variants
    LLM-generated rephrasings, fused via RRF. Uses reranked_search as
    the underlying retrieval method (Module 4's full pipeline) for
    each variant.

    Costs one LLM call for expansion, on top of n_variants+1 full
    hybrid+rerank searches — meaningfully slower/costlier than
    /search/reranked. Opt-in by design; not used automatically by
    /search or /ask.
    """
    query = preprocess_query(req.query)
    filters = build_filters(req.court, req.year, req.document_type)
    results = multi_query_search(
        query,
        search_fn=reranked_search,
        n_variants=req.n_variants,
        n_results=req.n_results,
        filters=filters,
    )
    return {"query": query, "filters": filters, "results": results}


class AskRequest(BaseModel):
    query: str
    n_passages: int = 5
    court: Optional[str] = None
    year: Optional[int] = None
    document_type: Optional[str] = None


@app.post("/ask")
def ask(req: AskRequest):
    query = preprocess_query(req.query)
    filters = build_filters(req.court, req.year, req.document_type)
    return answer_question(query, n_passages=req.n_passages, filters=filters)


@app.get("/documents/{filename}")
def get_document_endpoint(filename: str, court: Optional[str] = None):
    """
    Module 7 prerequisite — serves full judgment text + metadata for
    the Judgment Viewer page. `filename` is the source PDF filename
    exactly as it appears in a chunk's metadata.source_filename
    (e.g. "c.a._106_k_2024.pdf"), typically obtained from a prior
    search result. `court`, if known, narrows the lookup instead of
    scanning every court folder.
    """
    doc = get_document(filename, court=court)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found")
    return doc
