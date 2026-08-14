"""
Centralized environment variable access for the AI service.

Mirrors backend/src/config/env.js: one place to read env vars from,
instead of scattering os.getenv() calls across the codebase. Reads
from the repo-root .env file, shared with the other services.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# app/config.py -> app/ -> ai-service/ -> repo root
ROOT_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ROOT_ENV_PATH)


class Settings:
    node_env: str = os.getenv("NODE_ENV", "development")
    port: int = int(os.getenv("AI_SERVICE_PORT", "8000"))
    embedding_model_name: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
    )


settings = Settings()
