# AI Service

Python / FastAPI application.

**Status:** Health check + embedding generation implemented
(Module 3, Session 3.1). No vector database, retrieval, or RAG yet.

## Structure

```text
ai-service/
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py         FastAPI app instance + GET /health
│   ├── config.py         centralized environment variable access
│   └── embeddings.py     wraps the embedding model (Session 3.1)
└── scripts/
    └── test_embeddings.py   standalone smoke test against real chunk data
```

## Setup

```bash
cd ai-service
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## Test it

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{ "status": "ok", "service": "ai-service", "timestamp": "..." }
```

FastAPI also gives you free interactive API docs once it's running,
at `http://localhost:8000/docs`.

## Embedding generation (Session 3.1)

```bash
python scripts/test_embeddings.py   # Windows: py scripts/test_embeddings.py
```

This loads the embedding model, embeds a couple of real chunks from
your Module 2 output (`ingestion/data/chunks/`), and checks that two
chunks from the **same** judgment come out more similar to each
other than a chunk from a completely unrelated one — a basic sanity
check that the embeddings are actually meaningful, not just present.

**Model:** `sentence-transformers/all-MiniLM-L6-v2` (set via
`EMBEDDING_MODEL_NAME` in `.env`) — small (~80MB), fast enough for
CPU, free, runs locally. Not fine-tuned for legal text specifically,
but a solid general-purpose default; swappable later via that one
env var without touching any code.

**First run will be slower** — it downloads the model weights from
Hugging Face once, then caches them locally.

**Important — I couldn't run this myself.** My sandbox has no
network access to install `sentence-transformers`/`torch` (a much
heavier dependency than anything used so far), so this was
syntax-checked and the surrounding logic (file loading, similarity
math) was verified with a stubbed-out model — but the actual model
loading and encoding needs to be confirmed on your machine. Please
run it and share the output.

## Notes

- Reads configuration from the **root** `.env` file, same pattern as
  the backend — see `app/config.py`.
- Dependencies are added only in the sessions that actually need
  them — `sentence-transformers` just arrived with Session 3.1.
  ChromaDB, BM25, and reranker libraries will follow in their own
  sessions, so `requirements.txt` always reflects what's really in
  use, not what might be needed eventually.
