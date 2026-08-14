# AI Service

Python / FastAPI application.

**Status:** Health check, embedding generation, vector storage
(ChromaDB), and basic semantic search implemented (Module 3,
Sessions 3.1–3.3). No keyword search (BM25), hybrid retrieval, or
reranking yet.

## Structure

```text
ai-service/
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py            FastAPI app: GET /health, POST /search
│   ├── config.py           centralized environment variable access
│   ├── embeddings.py       wraps the embedding model (Session 3.1)
│   ├── vector_store.py     wraps ChromaDB (Session 3.2)
│   └── search.py           semantic search (Session 3.3)
└── scripts/
    ├── test_embeddings.py       standalone embedding smoke test
    └── build_vector_index.py   embeds all chunks, loads into ChromaDB
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

## Build the vector index (Session 3.2)

```bash
python scripts/build_vector_index.py   # Windows: py scripts/build_vector_index.py
```

Reads every `.jsonl` file in `ingestion/data/chunks/` (Module 2's
output), embeds each chunk, and stores it in ChromaDB — a local,
file-based vector database (no separate server needed) that persists
to `ai-service/chroma_data/` (gitignored). Safe to re-run: it
`upsert`s by `chunk_id`, so re-running after reprocessing PDFs
updates existing entries instead of duplicating them.

**Metadata note:** ChromaDB only accepts string/int/float/bool
metadata values — no `None`, no lists. The `judges` field (a list)
gets joined into a comma-separated string before storage; fields
that are `None` (like a missing `case_number`) are dropped entirely
rather than stored as null. This was verified against real chunk
data before being trusted.

## Search it (Session 3.3)

Once the index is built, start the server:

```bash
uvicorn app.main:app --reload --port 8000
```

Then either use the interactive docs at `http://localhost:8000/docs`,
or:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "maintenance after khula", "n_results": 5}'
```

Returns the most semantically similar chunks, each with its full
metadata and a similarity score (0-1, higher = more similar). This
is **dense/semantic search only** — no keyword matching, filtering,
or reranking yet (Module 4).

**Also untested by me** — same limitation as embeddings: no network
to install `chromadb` here. All plumbing (metadata sanitization,
batching, the search round-trip) was verified with a stubbed vector
store against your real chunk data, but the real ChromaDB behavior
needs confirming on your machine.

## Notes

- Reads configuration from the **root** `.env` file, same pattern as
  the backend — see `app/config.py`.
- Dependencies are added only in the sessions that actually need
  them — `sentence-transformers` just arrived with Session 3.1.
  ChromaDB, BM25, and reranker libraries will follow in their own
  sessions, so `requirements.txt` always reflects what's really in
  use, not what might be needed eventually.
