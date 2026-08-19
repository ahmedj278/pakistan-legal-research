"""
FastAPI entry point for the AI service.

Health check (Module 1), semantic search, BM25 keyword search,
metadata filtering (Module 3), and hybrid retrieval via RRF fusion
(Module 4, Sessions 4.1-4.2). No reranking yet — Session 4.3.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from app.config import settings
from app.search import semantic_search
from app.bm25_search import keyword_search
from app.hybrid_search import hybrid_search
from app.reranked_search import reranked_search
from app.filters import build_filters

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
    filters = build_filters(req.court, req.year, req.document_type)
    results = semantic_search(req.query, n_results=req.n_results, filters=filters)
    return {"query": req.query, "filters": filters, "results": results}


@app.post("/search/keyword")
def search_keyword(req: SearchRequest):
    filters = build_filters(req.court, req.year, req.document_type)
    results = keyword_search(req.query, n_results=req.n_results, filters=filters)
    return {"query": req.query, "filters": filters, "results": results}


@app.post("/search/hybrid")
def search_hybrid(req: SearchRequest):
    filters = build_filters(req.court, req.year, req.document_type)
    results = hybrid_search(req.query, n_results=req.n_results, filters=filters)
    return {"query": req.query, "filters": filters, "results": results}


@app.post("/search/reranked")
def search_reranked(req: SearchRequest):
    filters = build_filters(req.court, req.year, req.document_type)
    results = reranked_search(req.query, n_results=req.n_results, filters=filters)
    return {"query": req.query, "filters": filters, "results": results}
