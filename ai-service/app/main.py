"""
FastAPI entry point for the AI service.

Health check (Module 1), semantic search, BM25 keyword search,
metadata filtering (Module 3), hybrid retrieval + reranking
(Module 4), and a basic RAG endpoint (Module 5, Session 5.2).
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
from app.rag import answer_question
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


class AskRequest(BaseModel):
    query: str
    n_passages: int = 5
    court: Optional[str] = None
    year: Optional[int] = None
    document_type: Optional[str] = None


@app.post("/ask")
def ask(req: AskRequest):
    filters = build_filters(req.court, req.year, req.document_type)
    return answer_question(req.query, n_passages=req.n_passages, filters=filters)
