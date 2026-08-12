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

🚧 Early development. Being built progressively, module by module.
See [Roadmap](#roadmap) below for what exists so far.

## Why this project

Searching large collections of Pakistani judgments manually is slow
and imprecise. This project explores how modern information
retrieval (BM25 + dense vector search + reranking) combined with
retrieval-augmented generation can make that search faster and more
useful, while staying honest about its limitations — no invented
case law, no fabricated citations, and explicit "insufficient
evidence" responses when the corpus doesn't support a confident
answer.

## Planned architecture

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
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
          Vector DB       BM25        Reranker
              |             |             |
              +-------------+-------------+
                            |
                            v
                           LLM
```

## Tech stack (planned)

| Layer       | Technology                       |
|-------------|-----------------------------------|
| Frontend    | React                              |
| Backend     | Node.js / Express                  |
| AI service  | Python / FastAPI                   |
| Retrieval   | ChromaDB + BM25 + cross-encoder reranker |
| Database    | PostgreSQL                         |
| Infra       | Docker / Docker Compose            |

## Repository structure

```text
pakistan-legal-research/
│
├── frontend/       React application
├── backend/        Node/Express application
├── ai-service/     Python/FastAPI application (retrieval, RAG)
├── ingestion/       Document processing pipeline
├── docs/           Architecture notes, evaluation results, diagrams
│
├── .env.example    Environment variable template (copy to .env)
├── .gitignore
└── README.md
```

Each subdirectory has its own README describing its purpose in more
detail.

## Getting started

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

Each service also has its own README with instructions for running
it directly on your machine (without Docker) if you'd rather do
that — see `backend/README.md`, `ai-service/README.md`, and
`frontend/README.md`.

No application functionality exists yet beyond health checks —
Postgres isn't used by any code yet either (that starts in Module 2).
This just proves the whole stack boots together.

## Roadmap

This project is being built in modules, with one focused session at
a time:

1. **Project foundation** — repo structure, backend/frontend/AI
   service skeletons, Docker setup *(in progress)*
2. **Legal document ingestion** — PDF → structured, chunked documents
3. **Search infrastructure** — dense + sparse retrieval, metadata filtering
4. **Hybrid retrieval and reranking**
5. **RAG and citation grounding**
6. **Query intelligence** — query rewriting/expansion, routing
7. **Web application** — search UI, judgment viewer, research mode
8. **Integration, evaluation, and deployment**

Detailed session-by-session progress and technical write-ups will
live in `docs/` as each module is completed.

## Limitations

This section will be filled in honestly as the system is built —
covering corpus size, OCR quality, metadata completeness, retrieval
limitations, and LLM limitations. No benchmark numbers will be
reported unless they were actually measured on this system.

## Disclaimer

This tool is for legal research and educational purposes only. It
does not constitute legal advice, and its outputs should not be
relied upon as a substitute for consultation with a qualified legal
professional.
