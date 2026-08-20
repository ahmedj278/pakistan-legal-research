"""
Centralized environment variable access for the AI service.

Mirrors backend/src/config/env.js: one place to read env vars from,
instead of scattering os.getenv() calls across the codebase. Reads
from the repo-root .env file, shared with the other services.

Uses `os.getenv(KEY) or default` rather than `os.getenv(KEY, default)`
everywhere below — deliberately. The two-argument form only falls
back when the key is completely ABSENT from .env; if the key exists
but is set to an empty string (e.g. "EMBEDDING_MODEL_NAME=" with
nothing after it — exactly what caused the Session 3.1 bug where the
embedding model silently failed to load), `os.getenv(KEY, default)`
still returns the empty string, not the default. `or` catches both
cases.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# app/config.py -> app/ -> ai-service/ -> repo root
AI_SERVICE_DIR = Path(__file__).resolve().parent.parent
ROOT_ENV_PATH = AI_SERVICE_DIR.parent / ".env"
load_dotenv(dotenv_path=ROOT_ENV_PATH)


class Settings:
    node_env: str = os.getenv("NODE_ENV") or "development"
    port: int = int(os.getenv("AI_SERVICE_PORT") or "8000")
    embedding_model_name: str = (
        os.getenv("EMBEDDING_MODEL_NAME") or "sentence-transformers/all-MiniLM-L6-v2"
    )

    # Defaults to a folder inside ai-service/ regardless of what
    # directory a script happens to be run from — a relative path in
    # .env would resolve differently depending on current working
    # directory, which is exactly the kind of thing worth avoiding.
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR") or str(
        AI_SERVICE_DIR / "chroma_data"
    )
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME") or "pk_judgments"

    reranker_model_name: str = (
        os.getenv("RERANKER_MODEL_NAME") or "cross-encoder/ms-marco-MiniLM-L-6-v2"
    )

    llm_provider: str = os.getenv("LLM_PROVIDER") or "gemini"
    llm_model_name: str = os.getenv("LLM_MODEL_NAME") or "gemini-2.5-flash"
    llm_api_key: str = os.getenv("LLM_API_KEY") or ""


settings = Settings()
