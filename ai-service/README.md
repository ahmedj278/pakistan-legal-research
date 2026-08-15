# AI Service

Python / FastAPI application.

**Status:** Health check, embedding generation, vector storage
(ChromaDB), semantic search, BM25 keyword search, and metadata
filtering implemented (Module 3, Sessions 3.1–3.5 — Module 3
complete). No hybrid fusion or reranking yet — that's Module 4.

## Structure

```text
ai-service/
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py            FastAPI app: /health, /search, /search/keyword
│   ├── config.py           centralized environment variable access
│   ├── chunk_loader.py     shared loader for Module 2's chunk output
│   ├── embeddings.py       wraps the embedding model (Session 3.1)
│   ├── vector_store.py     wraps ChromaDB (Session 3.2)
│   ├── search.py           semantic search (Session 3.3)
│   ├── bm25_search.py      BM25 keyword search (Session 3.4)
│   └── filters.py          metadata filtering, shared by both (Session 3.5)
└── scripts/
    ├── test_embeddings.py       standalone embedding smoke test
    ├── build_vector_index.py   embeds all chunks, loads into ChromaDB
    └── build_bm25_index.py     builds the BM25 keyword index
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

## Keyword search (Session 3.4)

```bash
python scripts/build_bm25_index.py   # Windows: py scripts/build_bm25_index.py
```

Builds a BM25 index over the same chunk data, saved to
`ai-service/bm25_index.pkl` (gitignored). Much faster than building
the vector index — no embedding model involved, just tokenizing and
counting term frequencies. Unlike the vector index, this always
rebuilds from scratch when re-run, since BM25 needs corpus-wide term
statistics rather than supporting a per-document upsert.

Query it the same way as semantic search, at a separate endpoint:

```bash
curl -X POST http://localhost:8000/search/keyword \
  -H "Content-Type: application/json" \
  -d '{"query": "khula maintenance", "n_results": 5}'
```

**Why a separate endpoint instead of merging into `/search`:**
Module 4 combines both into hybrid retrieval, but the roadmap
explicitly wants to be able to compare dense-only, BM25-only,
hybrid, and hybrid+reranking against each other — keeping them
separately callable now is what makes that comparison possible
later, rather than something to refactor in afterward.

**Why BM25 matters here specifically:** manual testing of semantic
search alone (see `docs/retrieval-notes.md`) found it drifts toward
generically-similar content when no real semantic match exists,
rather than finding nothing. A query for a specific literal term
(a case number, a specific legal term) is exactly what BM25 is
built for — if the word exists anywhere in the corpus, BM25 finds it
directly, with no drift possible.

**Tested properly this time** — `rank_bm25` is pure Python, so
unlike `chromadb`/`sentence-transformers` I could actually
reimplement the real BM25 algorithm locally and run a genuine
end-to-end test against your real chunk data (not a stub): querying
"promotion" correctly ranked chunks that actually contain the word,
and a nonsense query correctly scored 0.000 everywhere rather than
returning a fabricated match. Still worth confirming the real
`rank_bm25` package installs and runs identically on your machine,
but this one has real confidence behind it, not just a syntax check.

## Metadata filtering (Session 3.5)

Both `/search` and `/search/keyword` now accept optional filters,
using the metadata Module 2 already extracted:

```bash
curl -X POST http://localhost:8000/search/keyword \
  -H "Content-Type: application/json" \
  -d '{"query": "promotion", "court": "islamabad_high_court"}'
```

Available filter fields: `court` (internal slug —
`"supreme_court"` / `"islamabad_high_court"`, not the display name),
`year`, `document_type` (`"JUDGMENT"` / `"ORDER_SHEET"`). Any
combination can be used together; omitted fields aren't filtered on.

Implemented once, shared by both search methods (`app/filters.py`),
so filtering behaves identically regardless of which retrieval
method is used — matters once Module 4 combines them, since a
filter shouldn't behave differently depending on which underlying
method produced a given result.

**Tested against real chunk data**: filtering a `"promotion"` query
down to `court=islamabad_high_court` correctly returned 0 results
(that content only exists in the Supreme Court sample), and the
Chroma `where`-clause builder was verified to produce the exact
shape ChromaDB expects for both single and combined filters.

## Comparing embedding models

Two models are registered for comparison (`app/model_registry.py`):
`sentence-transformers/all-MiniLM-L6-v2` (general-purpose, 384d) and
`nlpaueb/legal-bert-base-uncased` (legal-domain, 768d). Each gets
its own ChromaDB collection — vectors from different models aren't
comparable, so they're never mixed.

```bash
python scripts/build_vector_index.py           # builds ALL registered models
python scripts/build_vector_index.py minilm    # or just one, by key
python scripts/compare_embedding_models.py     # runs default test queries against both
python scripts/compare_embedding_models.py "your own query"
```

`nlpaueb/legal-bert-base-uncased` is a **plain BERT checkpoint**,
not a purpose-built sentence-embedding model — it has no
`modules.json`/pooling config of its own. `sentence-transformers`
handles this automatically: loading a plain transformer model with
no sentence-embedding config triggers an automatic fallback to a
Transformer + mean-Pooling module (confirmed directly against the
official sentence-transformers docs before relying on it) — so this
works with zero extra code, but it's worth knowing this fallback is
happening rather than assuming the model was purpose-built for this.

**Expect this one to be slower and heavier**: ~440MB vs MiniLM's
~80MB, BERT-base size. Embedding all 1803 chunks will take
meaningfully longer than MiniLM's ~107s — plausibly 10-20 minutes on
CPU. Should still run fine on 8GB RAM, just budget the time.

**Untested by me, same limitation as before** — no network here to
install either model. The multi-model plumbing itself (separate
collections, correct per-model dimensions, no cross-contamination)
was verified against your real chunk data with both models stubbed
out; the actual model behavior and comparison results need
confirming on your machine.

## Notes

- Reads configuration from the **root** `.env` file, same pattern as
  the backend — see `app/config.py`.
- Dependencies are added only in the sessions that actually need
  them — `chunk_loader.py` is shared between the vector and BM25
  build scripts to avoid duplicating that logic twice.
