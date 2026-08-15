"""
Embedding generation (Module 3, Session 3.1; extended for
multi-model comparison).

Wraps sentence-transformers behind a small interface, so the actual
embedding model can be swapped later (a different local model, or a
hosted API) without changing any code that calls embed_texts() —
matches the project's modularity goal.

Every function accepts an optional `model_name` override, defaulting
to `settings.embedding_model_name` (the "primary" model) when not
given. This is what lets scripts/compare_embedding_models.py embed
the same text with several different models in one process, to
compare a general-purpose model against a legal-domain one — see
app/model_registry.py for the models being compared and why.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=4)
def get_model(model_name: str = None) -> SentenceTransformer:
    # Cached per model_name, so comparing multiple models in one
    # process only loads each one from disk once, not on every call.
    model_name = model_name or settings.embedding_model_name
    return SentenceTransformer(model_name)


def embed_texts(texts: list, model_name: str = None) -> list:
    """Takes a list of strings, returns a list of embedding vectors
    (each a list of floats), in the same order."""
    model = get_model(model_name)
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


def embedding_dimension(model_name: str = None) -> int:
    return get_model(model_name).get_sentence_embedding_dimension()
