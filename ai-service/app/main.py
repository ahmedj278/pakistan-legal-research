"""
FastAPI entry point for the AI service.

Health check (Module 1), semantic search, BM25 keyword search,
metadata filtering (Module 3), hybrid retrieval + reranking
(Module 4), RAG (Module 5), query preprocessing + expansion
(Module 6), and document retrieval (Module 7 prerequisite).

Query preprocessing (6.1, free/instant) is applied here, at the API
boundary, to every incoming query on every endpoint below — this is
the one place raw user text actually enters the system, so it's the
right place to clean it once rather than duplicating the call inside
every individual search function.

Query expansion (6.2, costs one extra LLM call) is intentionally NOT
applied automatically to /search or /ask — it's exposed as its own
opt-in endpoint, /search/expanded, so it doesn't silently double API
quota usage on every request.

Module 8 additions: request validation (bounded n_results/n_passages/
n_variants, rejected empty queries, restricted court/document_type to
actual known values instead of any string) and structured logging
(request-level INFO logs, a global exception handler that logs
unhandled errors with a traceback instead of a bare stack trace mixed
into uvicorn's access log).
"""

import logging
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.search import semantic_search
from app.bm25_search import keyword_search
from app.hybrid_search import hybrid_search
from app.reranked_search import reranked_search
from app.rag import answer_question
from app.filters import build_filters
from app.query_processing import preprocess_query, multi_query_search
from app.documents import get_document

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pakistan Legal Research - AI Service",
    description="Handles document processing, retrieval, and RAG.",
    version="0.1.0",
)


@app.exception_handler(Exception)
async def log_unhandled_exceptions(request: Request, exc: Exception):
    """
    Without this, an unhandled error just becomes a bare stack trace
    mixed into uvicorn's per-request access log — easy to miss and
    hard to correlate with which request caused it. This logs it
    clearly (with the path, for correlation) before returning the
    same generic 500 FastAPI would have returned anyway; it doesn't
    change behavior, only visibility.
    """
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


# Known court slugs and document types — confirmed against
# ingestion/src/config.py and ingestion/src/metadata.py's
# detect_document_type() respectively, not guessed. Using Literal
# here (rather than a bare `str`) means a typo'd or nonexistent
# value gets a clear 422 from FastAPI, instead of silently matching
# zero documents the way build_filters() would otherwise allow.
CourtSlug = Literal["supreme_court", "islamabad_high_court"]
DocumentType = Literal["JUDGMENT", "ORDER_SHEET", "UNKNOWN"]

# All Pakistani court judgments postdate 1947 (the founding of
# Pakistan) — a real, defensible lower bound, not an arbitrary
# round number.
MIN_JUDGMENT_YEAR = 1947
MAX_JUDGMENT_YEAR = datetime.now().year + 1


def _clean_query_or_400(raw_query: str) -> str:
    """
    Shared by every search/ask endpoint below: preprocesses the query
    and rejects it with a clear 400 if nothing meaningful is left.
    Pydantic's Field(min_length=1) alone isn't enough here, since a
    whitespace-only string like "   " passes that check but becomes
    "" after preprocess_query()'s cleanup — this catches that case
    explicitly instead.
    """
    query = preprocess_query(raw_query)
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    return query


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    # Upper bound of 50 protects the reranker specifically — it's a
    # CPU-bound cross-encoder that scores every candidate, so a much
    # larger request would meaningfully slow down /search/reranked
    # and /search/expanded for no real benefit (nobody reads 500
    # search results).
    n_results: int = Field(default=5, ge=1, le=50)
    # Optional metadata filters (Session 3.5).
    court: Optional[CourtSlug] = None
    year: Optional[int] = Field(default=None, ge=MIN_JUDGMENT_YEAR, le=MAX_JUDGMENT_YEAR)
    document_type: Optional[DocumentType] = None


@app.post("/search")
def search(req: SearchRequest):
    query = _clean_query_or_400(req.query)
    filters = build_filters(req.court, req.year, req.document_type)
    logger.info(f"POST /search query={query!r} filters={filters}")
    results = semantic_search(query, n_results=req.n_results, filters=filters)
    return {"query": query, "filters": filters, "results": results}


@app.post("/search/keyword")
def search_keyword(req: SearchRequest):
    query = _clean_query_or_400(req.query)
    filters = build_filters(req.court, req.year, req.document_type)
    logger.info(f"POST /search/keyword query={query!r} filters={filters}")
    results = keyword_search(query, n_results=req.n_results, filters=filters)
    return {"query": query, "filters": filters, "results": results}


@app.post("/search/hybrid")
def search_hybrid(req: SearchRequest):
    query = _clean_query_or_400(req.query)
    filters = build_filters(req.court, req.year, req.document_type)
    logger.info(f"POST /search/hybrid query={query!r} filters={filters}")
    results = hybrid_search(query, n_results=req.n_results, filters=filters)
    return {"query": query, "filters": filters, "results": results}


@app.post("/search/reranked")
def search_reranked(req: SearchRequest):
    query = _clean_query_or_400(req.query)
    filters = build_filters(req.court, req.year, req.document_type)
    logger.info(f"POST /search/reranked query={query!r} filters={filters}")
    results = reranked_search(query, n_results=req.n_results, filters=filters)
    return {"query": query, "filters": filters, "results": results}


class ExpandedSearchRequest(SearchRequest):
    # Upper bound of 10 matches expand_query()'s own reasonable range
    # (see app/query_processing.py) — beyond that, each extra variant
    # is another full hybrid+rerank search AND the LLM is being asked
    # to generate more rephrasings in one fixed-length (max_tokens=200)
    # response, which would just start truncating.
    n_variants: int = Field(default=3, ge=1, le=10)


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
    query = _clean_query_or_400(req.query)
    filters = build_filters(req.court, req.year, req.document_type)
    logger.info(f"POST /search/expanded query={query!r} filters={filters} n_variants={req.n_variants}")
    results = multi_query_search(
        query,
        search_fn=reranked_search,
        n_variants=req.n_variants,
        n_results=req.n_results,
        filters=filters,
    )
    return {"query": query, "filters": filters, "results": results}


class AskRequest(BaseModel):
    query: str = Field(min_length=1)
    # Upper bound of 20: passing many more passages than that into
    # the LLM's context is mostly wasted tokens/cost/latency for a
    # RAG answer, not a meaningful accuracy gain.
    n_passages: int = Field(default=5, ge=1, le=20)
    court: Optional[CourtSlug] = None
    year: Optional[int] = Field(default=None, ge=MIN_JUDGMENT_YEAR, le=MAX_JUDGMENT_YEAR)
    document_type: Optional[DocumentType] = None


@app.post("/ask")
def ask(req: AskRequest):
    query = _clean_query_or_400(req.query)
    filters = build_filters(req.court, req.year, req.document_type)
    logger.info(f"POST /ask query={query!r} filters={filters}")
    return answer_question(query, n_passages=req.n_passages, filters=filters)


@app.get("/documents/{filename}")
def get_document_endpoint(filename: str, court: Optional[CourtSlug] = None):
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
        logger.warning(f"GET /documents/{filename} (court={court}) -> not found")
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found")
    return doc
