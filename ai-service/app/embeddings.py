"""
Embedding generation (Module 3, Session 3.1).

Wraps sentence-transformers behind a small interface, so the actual
embedding model can be swapped later (a different local model, or a
hosted API) without changing any code that calls embed_texts() —
matches the project's modularity goal.

Model choice: sentence-transformers/all-MiniLM-L6-v2. Reasoning:
- Small (~80MB) and fast enough to run on CPU — no GPU required,
  which matters since this needs to run on a normal laptop.
- 384-dimensional vectors — smaller than most alternatives, which
  keeps the vector database lighter (relevant once this scales from
  100 sample judgments to the full ~8,000).
- Free, runs locally, no API key or per-request cost.
- Well-established as a solid general-purpose default; not
  fine-tuned for legal text specifically, but that's a reasonable
  starting point given the "not aiming for perfection" scope — a
  legal-domain embedding model could be swapped in later via
  EMBEDDING_MODEL_NAME alone, without touching this file.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    # Cached so the model is loaded from disk once per process
    # (this takes a few seconds) rather than on every call.
    return SentenceTransformer(settings.embedding_model_name)


def embed_texts(texts: list) -> list:
    """Takes a list of strings, returns a list of embedding vectors
    (each a list of floats), in the same order."""
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


def embedding_dimension() -> int:
    return get_model().get_sentence_embedding_dimension()
