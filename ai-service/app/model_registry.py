"""
Embedding model registry (Module 3, follow-up to Session 3.1-3.2).

Maps each embedding model being compared to its own ChromaDB
collection name, so switching or comparing models never means
overwriting or mixing another model's vectors — a query embedded
with one model is meaningless compared against vectors from another
model (different vector space entirely), so each needs an
independent collection.

To compare a new model later: add an entry here, run
scripts/build_vector_index.py (it builds every registered model),
then scripts/compare_embedding_models.py.
"""

EMBEDDING_MODELS = {
    "minilm": {
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "collection_name": "pk_judgments_minilm",
        "description": "General-purpose, 384d, ~80MB (Session 3.1 default)",
    },
    "legalbert_st": {
        "model_name": "IoannisKat1/legal-bert-base-uncased-legal-matryoshka",
        "collection_name": "pk_judgments_legalbert_st",
        "description": "Legal-domain BERT, 768d — properly fine-tuned as a sentence "
        "embedder (not an auto-pooled raw checkpoint). Chosen over "
        "'legalbert' (nlpaueb/legal-bert-base-uncased) after evaluation "
        "showed the raw checkpoint scoring meaningfully worse (Recall@1 "
        "0.4-0.6 vs this model's 0.8) — see docs/retrieval-notes.md.",
    },
}
