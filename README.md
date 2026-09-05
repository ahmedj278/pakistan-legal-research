# Pakistan Legal Research Platform

An AI-powered research tool for searching and exploring Pakistani
court judgments, combining keyword search, semantic (vector) search,
hybrid retrieval, reranking, and citation-grounded RAG.

> **This is a legal research / educational tool. It does not provide
> legal advice**, and it is designed to never fabricate citations or
> present LLM-generated answers as authoritative on their own —
> every answer is meant to be traceable back to retrieved source
> passages.

## Status

Modules 1–7 are complete and working end-to-end: ingestion, search
(keyword/semantic/hybrid/reranked), citation-grounded RAG, query
preprocessing/expansion/routing, and the full web app (search,
research mode, judgment viewer). Module 8 (integration, evaluation,
deployment) is in progress — see the [Roadmap](#roadmap) for exactly
what's done and what's left.

## Why this project

Searching large collections of Pakistani judgments manually is slow
and imprecise. This project explores how modern information
retrieval (BM25 + dense vector search + reranking) combined with
retrieval-augmented generation can make that search faster and more
useful, while staying honest about its limitations — no invented
case law, no fabricated citations, and explicit "insufficient
evidence" responses when the corpus doesn't support a confident
answer.

## Architecture

```text
React frontend
      |
      v
Node.js + Express backend
      |
      +--------------------+
      |                    |
      v                    v
 PostgreSQL          FastAPI AI service
  (not yet used)            |
              +-------------+-------------+
              |             |             |
              v             v             v
          Vector DB       BM25        Reranker
         (ChromaDB)   (rank-bm25)  (cross-encoder)
              |             |             |
              +-------------+-------------+
                            |
                            v
                     LLM (Gemini / Anthropic /
                       local Ollama for testing)
```

The backend is a thin proxy — all retrieval and RAG logic lives in
the AI service (Python/FastAPI). Postgres is provisioned but not yet
used by any application code (no user accounts or saved-judgment
features have been built — see Limitations).

## Tech stack

| Layer       | Technology                       |
|-------------|-----------------------------------|
| Frontend    | React + React Router, plain CSS    |
| Backend     | Node.js / Express                  |
| AI service  | Python / FastAPI                   |
| Retrieval   | ChromaDB + BM25 (rank-bm25) + cross-encoder reranker |
| LLM         | Gemini (default, free tier) / Anthropic / local Ollama (testing only) |
| Database    | PostgreSQL (provisioned, not yet used) |
| Testing     | pytest (ai-service) + Vitest/React Testing Library (frontend) |
| Infra       | Docker / Docker Compose            |

## Repository structure

```text
pakistan-legal-research/
│
├── frontend/        React application (pages/, components/, api/, *.test.jsx)
├── backend/         Node/Express application (thin proxy to ai-service)
├── ai-service/       Python/FastAPI application (retrieval, RAG, tests/)
├── ingestion/        Document processing pipeline
├── docs/            Architecture notes, evaluation results, diagrams
│
├── .env.example     Environment variable template (copy to .env)
├── .gitignore
└── README.md
```

Each subdirectory has its own README describing its purpose in more
detail.

## Getting started

### With Docker

Requires [Docker](https://docs.docker.com/get-docker/) (with Compose
included, as it is in current Docker Desktop).

```bash
cp .env.example .env
docker compose up --build
```

Then:

| Service    | URL                          |
|------------|-------------------------------|
| Frontend   | http://localhost:5173         |
| Backend    | http://localhost:4000/health  |
| AI service | http://localhost:8000/health  |
| Postgres   | localhost:5432                |

### Without Docker (manual, four terminals)

```bash
# 1. (optional) local LLM for free/offline testing — skip if using
#    Gemini/Anthropic and the desktop app isn't already running
ollama serve

# 2. AI service
cd ai-service
uvicorn app.main:app --reload --port 8000

# 3. Backend
cd backend
npm run dev

# 4. Frontend
cd frontend
npm run dev
```

Each service also has its own README with more detail — see
`backend/README.md`, `ai-service/README.md`, and `frontend/README.md`.

## Example workflow

**Search mode** — type a query (a topic like "maintenance after
khula", or a citation like "PLD 2024 SC 1276") and get back ranked
judgment excerpts with case metadata, a relevance score, and a link
to the full judgment.

**Research mode** — ask a full question ("Can a wife get maintenance
after khula?") and get a generated answer with inline `[1]`, `[2]`
citations, each backed by a real retrieved passage you can click
through to verify. If the model can't ground its answer in the
retrieved passages, that's surfaced as a visible warning rather than
presented as a confident, sourced answer.

## Testing

```bash
# ai-service (47 tests)
cd ai-service
pytest tests/ -v

# frontend (25 tests)
cd frontend
npx vitest run
```

## Roadmap

1. ✅ **Project foundation** — repo structure, backend/frontend/AI service skeletons, Docker setup
2. ✅ **Legal document ingestion** — PDF → structured, chunked documents
3. ✅ **Search infrastructure** — dense + sparse retrieval, metadata filtering
4. ✅ **Hybrid retrieval and reranking**
5. ✅ **RAG and citation grounding**
6. ✅ **Query intelligence** — preprocessing, expansion, citation-lookup routing
7. ✅ **Web application** — search UI, judgment viewer, research mode
8. 🚧 **Integration, evaluation, and deployment**
   - ✅ Test suites committed (47 pytest + 25 Vitest)
   - ✅ Request validation (bounded params, real value restrictions) and structured logging
   - ✅ Docker Compose
   - ✅ Retrieval evaluation (Recall@K / MRR) — see Limitations for actual numbers
   - ⬜ RAG evaluation (`scripts/evaluate_rag.py` is built; not yet run to completion — see Limitations)
   - ⬜ Architecture diagram, screenshots
   - Authentication: deliberately skipped — no user-account or saved-judgment feature exists to need it

Detailed session-by-session progress and technical write-ups live in
`docs/` — in particular `docs/retrieval-notes.md`, which documents
the full evolution of the retrieval evaluation, including two real
bugs found and fixed along the way.

## Limitations

**Corpus size and scope.** This is a portfolio-scale corpus, not an
exhaustive one — currently covers Supreme Court of Pakistan and
Islamabad High Court judgments only. Coverage of other high courts
is not yet built.

**Retrieval evaluation — real measured numbers, not estimates.**
The most rigorous run (`docs/retrieval-notes.md`, Test 7), on a
query set deliberately designed to avoid literal keyword overlap
with the correct answer:

| Method              | Recall@1 | Recall@3 | Recall@5 | MRR   |
|---------------------|----------|----------|----------|-------|
| BM25 alone           | 0.1      | 0.4      | 0.5      | 0.242 |
| MiniLM (semantic)    | 0.5      | 0.7      | 0.8      | 0.62  |
| legalbert_st (semantic) | 0.7   | 0.9      | 1.0      | 0.808 |
| Hybrid (BM25+MiniLM, RRF)   | 0.4 | 0.5      | 0.6      | 0.47  |
| Hybrid (BM25+legalbert_st, RRF) | 0.5 | 0.8  | 1.0      | 0.667 |

Two real findings from this: (1) BM25 alone is highly sensitive to
literal keyword overlap and collapses on paraphrased queries — this
is expected, not a bug. (2) Naive, unweighted RRF fusion is *not* a
free improvement: on this query set, the single best embedding
model (`legalbert_st`) actually outperformed hybrid fusion on every
metric except a tied Recall@5, because RRF gives BM25's confident
wrong answers equal weight to the stronger model's correct ones.

A separate, targeted test (Tests 8–9) found that the cross-encoder
reranker — while a general improvement for natural-language
questions — actively *hurts* citation-style queries specifically
(a real query's correct chunk was pushed from rank 4 to rank 11 by
reranking alone). This directly motivated Module 6, Session 6.3:
citation-shaped queries are now deterministically detected and
routed around the reranker.

**RAG (answer quality) evaluation — built, not yet run.**
`scripts/evaluate_rag.py` and `app/evaluation.py`'s `evaluate_rag()`
exist and are unit-tested, but a full run against the real LLM was
blocked by hitting the Gemini free-tier daily quota mid-evaluation.
No RAG-quality numbers are reported here because none have actually
been measured yet — this will be filled in with real numbers once a
full run completes, not estimated in the meantime.

**Small local model (Ollama) is for pipeline testing only.**
`gemma3:1b` via Ollama was used during development specifically to
test the pipeline's plumbing (retrieval → LLM → citation parsing →
grounding) without spending Gemini quota. It is not the production
default and its answer quality is not representative of the actual
system — the tiny model was observed to sometimes ignore the
`[N]` citation-format instruction entirely (writing out the raw
citation text instead), which the citation parser correctly
reports as "not grounded" rather than crashing on.

**Citation field is usually empty.** Pakistani courts typically
assign formal citations (e.g. "PLD 2024 SC 1276") after publication,
not at the time a judgment is issued — so the `citation` metadata
field is null for most documents in this corpus. The UI shows case
number instead, which is real but a different thing (see
`ResultCard.jsx`'s and `documents.py`'s docstrings).

**No authentication, saved judgments, or search history.** These
were explicitly out of scope per the project spec (marked optional)
— no user-account model exists, so there's nothing to authenticate
against.

## Disclaimer

This tool is for legal research and educational purposes only. It
does not constitute legal advice, and its outputs should not be
relied upon as a substitute for consultation with a qualified legal
professional.
