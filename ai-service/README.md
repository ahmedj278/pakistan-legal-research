# AI Service

Python / FastAPI application.

**Status:** Full retrieval pipeline complete — embeddings, vector
storage, semantic search, BM25, metadata filtering, hybrid RRF
fusion, and cross-encoder reranking (Module 3 complete; Module 4,
Sessions 4.1–4.3). Retrieval evaluation harness in place. No RAG/LLM
answer generation yet — that's Module 5.

## Structure

```text
ai-service/
├── requirements.txt
├── app/
│   ├── main.py              /health, /search, /search/keyword, /search/hybrid, /search/reranked
│   ├── config.py
│   ├── chunk_loader.py
│   ├── embeddings.py
│   ├── model_registry.py
│   ├── vector_store.py
│   ├── search.py             semantic search (3.3)
│   ├── bm25_search.py        BM25 (3.4)
│   ├── filters.py            metadata filtering (3.5)
│   ├── evaluation.py         Recall@K / MRR metrics
│   ├── hybrid_search.py      RRF fusion (4.1-4.2)
│   ├── reranker.py           cross-encoder wrapper (4.3)
│   └── reranked_search.py    full pipeline: BM25+semantic -> RRF -> rerank (4.3)
├── eval/
│   └── test_queries.json
└── scripts/
    ├── test_embeddings.py
    ├── build_vector_index.py
    ├── build_bm25_index.py
    ├── compare_embedding_models.py
    ├── evaluate_retrieval.py
    ├── find_documents_containing.py
    └── inspect_query_overlap.py
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

## Proper evaluation: Recall@K and MRR (brought forward from Session 4.4)

Single-query eyeballing turned out too unreliable to judge the
MiniLM-vs-LegalBERT comparison from — especially for "khula," a
non-English legal term neither model was specifically trained on,
where a bad result might mean "this model is worse" or might just
mean "this word is poorly represented in general." Formal evaluation
against known correct answers settles this properly.

```bash
python scripts/find_documents_containing.py khula
# lists which real documents actually contain the term, with case
# titles — use this to confirm/find entries for the test set below,
# without manually opening PDFs

python scripts/evaluate_retrieval.py
```

`eval/test_queries.json` holds the ground-truth set — each entry is
a query plus the filename(s) of documents known to actually be
relevant. **Currently only has 2 entries** (carried over from
earlier manual testing) — add more before trusting the numbers;
2 data points isn't enough to draw a real conclusion from. Aim for
5-10.

Reports Recall@1/3/5 and MRR for BM25 and every registered embedding
model, side by side. `app/evaluation.py` is deliberately generic
(takes any search function, not a specific implementation) — the
exact same evaluation will be reused once hybrid retrieval and
reranking exist (Module 4), to compare all four approaches with the
same metrics instead of rebuilding this.

**Verified with precisely controlled test cases** (not just real
data, since I need to know the *math* is right, not just that it
runs): a relevant result at rank 1 correctly gives Recall@1=1.0 and
MRR=1.0; a relevant result at rank 3 gives Recall@1=0, Recall@3=1.0,
MRR=0.333; a complete miss gives 0 across the board. The
`find_documents_containing.py` helper was also confirmed against
real chunk data — correctly found the right document for a known
term.

## Hybrid retrieval (Sessions 4.1-4.2)

```bash
curl -X POST http://localhost:8000/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{"query": "khula", "n_results": 5}'
```

Combines BM25 and semantic search using **Reciprocal Rank Fusion
(RRF)**: each method runs independently with a larger candidate
pool (20 by default) than requested, and results are combined by
**rank position**, not raw score — a BM25 score and a cosine
similarity aren't on the same scale, so averaging them directly
would be meaningless. A chunk found near the top of *both* lists
outranks one found in only one list, even if that one list ranked it
#1. Each result in the response includes an `rrf_score` reflecting
this combined rank, alongside its normal text/metadata.

Uses `settings.embedding_model_name` (the default embedding model)
for its semantic half — currently `minilm`.

**Verified two ways**: the RRF math itself was checked against a
hand-computed expected ranking (not just "does it run") — confirmed
exact score values and ordering. Then the full pipeline was run
end-to-end against real chunk data with a real BM25 index and
cosine-similarity-based fake embeddings, confirming genuinely
correct, sensibly-ranked results.

`scripts/evaluate_retrieval.py` now includes a `hybrid` row, so
Recall@K/MRR can be compared directly against BM25-only and
semantic-only — the actual point of building this, per your own
"test whether hybrid actually helps, don't assume it" conclusion
from manual testing.

## Reranking (Session 4.3)

```bash
curl -X POST http://localhost:8000/search/reranked \
  -H "Content-Type: application/json" \
  -d '{"query": "PLD 2024 SC 1276", "n_results": 5}'
```

Completes the full pipeline: BM25 + semantic search → RRF fusion →
**cross-encoder reranking**. Unlike RRF (which only combines rank
*positions*), a cross-encoder reads the query and each candidate
passage *together* and produces a direct relevance judgment — this
is what should fix the specific failure found in manual testing
(`docs/retrieval-notes.md`, Test 8): a citation-lookup query where
the literally-correct chunk was buried under superficially
citation-shaped noise by naive rank fusion.

Uses `sentence-transformers`' `CrossEncoder` — **no new dependency**,
it's the same package installed since Session 3.1. Model:
`cross-encoder/ms-marco-MiniLM-L-6-v2` (`RERANKER_MODEL_NAME` in
`.env`), a standard general-purpose reranker — not legal-tuned, same
documented limitation as the embedding model situation, swappable
later the same way.

**Verified with a real, non-random test**: a fake cross-encoder
scoring by genuine word overlap, given the exact Test 8 scenario
(correct chunk deliberately placed last) — confirmed it correctly
promotes the truly relevant chunk to #1. The full pipeline
(BM25+semantic → RRF → rerank) was also run end-to-end against real
chunk data, confirming both `rrf_score` and `rerank_score` survive
correctly through every stage.

`scripts/evaluate_retrieval.py` now includes `reranked+<model>` rows
for every registered embedding model — the real test of whether
reranking recovers what naive hybrid fusion lost (Test 7) and fixes
the citation-burying failure (Test 8), rather than assuming it does.

## Notes

- Reads configuration from the **root** `.env` file, same pattern as
  the backend — see `app/config.py`.
- Dependencies are added only in the sessions that actually need
  them — `chunk_loader.py` is shared between the vector and BM25
  build scripts to avoid duplicating that logic twice.
