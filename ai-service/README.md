# AI Service

Python / FastAPI application.

**Status:** Minimal skeleton implemented (Module 1, Session 1.3).
No retrieval, embeddings, or RAG logic yet — just app setup, config
loading, and a health check.

## Structure

```text
ai-service/
├── requirements.txt
└── app/
    ├── __init__.py
    ├── main.py      FastAPI app instance + GET /health
    └── config.py    centralized environment variable access
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

## Notes

- Reads configuration from the **root** `.env` file, same pattern as
  the backend — see `app/config.py`.
- Kept dependencies to the minimum needed to boot a server
  (`fastapi`, `uvicorn`, `python-dotenv`). Libraries for embeddings,
  ChromaDB, BM25, and the reranker will be added only in the
  sessions that actually use them (Module 3+), so it's always clear
  from `requirements.txt` what's really in use.
