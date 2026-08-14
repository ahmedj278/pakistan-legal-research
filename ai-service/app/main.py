"""
FastAPI entry point for the AI service.

Health check (Module 1) plus basic semantic search (Module 3,
Session 3.3). No keyword search, hybrid retrieval, reranking, or
RAG yet — those are Modules 4-5.
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

from app.config import settings
from app.search import semantic_search

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


@app.post("/search")
def search(req: SearchRequest):
    results = semantic_search(req.query, n_results=req.n_results)
    return {"query": req.query, "results": results}
