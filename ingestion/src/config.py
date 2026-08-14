"""
Configuration for the ingestion pipeline.

Reads from the repo-root .env, same pattern as backend/ai-service.
Each court gets its own source directory, since — as confirmed by
inspecting real samples — Supreme Court and Islamabad High Court
judgments use completely different templates and need separate
handling in later stages (metadata extraction especially).

Point INGESTION_SC_DIR / INGESTION_IHC_DIR at wherever your PDFs
actually live locally — they don't have to be inside this repo.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ROOT_ENV_PATH)

# Default to the ingestion/data/raw/<court> folders inside the repo
# if the env vars aren't set, so the pipeline still runs out of the
# box against a small local sample.
INGESTION_DIR = Path(__file__).resolve().parent.parent

SOURCE_DIRS = {
    "supreme_court": Path(
        os.getenv("INGESTION_SC_DIR", INGESTION_DIR / "data" / "raw" / "supreme_court")
    ),
    "islamabad_high_court": Path(
        os.getenv(
            "INGESTION_IHC_DIR", INGESTION_DIR / "data" / "raw" / "islamabad_high_court"
        )
    ),
}

OUTPUT_DIR = INGESTION_DIR / "data" / "processed"
LOG_DIR = INGESTION_DIR / "logs"

# Below this many extracted characters, a "successfully" extracted
# PDF is suspicious enough to flag rather than trust — most likely a
# scanned/image-only page that happened not to error out.
MIN_TEXT_LENGTH_THRESHOLD = 50
