# Project Handoff: Pakistan Legal Research Platform

Paste/upload this file as the FIRST message in a new chat, along
with your actual project folder (zipped) if possible, so Claude has
both the real code state and this narrative context.

## What this project is

AI-powered legal research platform for Pakistani court judgments
(Supreme Court + Islamabad High Court, ~100 sample PDFs so far, with
a real corpus of ~8,000 available to scale to later). Portfolio
project for a BSCS student, built session-by-session with meaningful
git commits after each one. Stack: React frontend, Node/Express
backend, Python/FastAPI AI service, PostgreSQL, ChromaDB, Docker
Compose.

## How we work together (IMPORTANT — follow this)

- I (the user) tell Claude which specific module/session to work on
  next — Claude should NOT jump ahead or implement future sessions
  unprompted.
- Claude should inspect the current repo state before changing
  anything (ask me to upload relevant files/folders if needed).
- After each session: explain what was built, key decisions, how to
  test it, a git commit message, and what's NOT built yet — then
  stop and wait.
- Claude should actually TEST code against real data where possible
  (not just syntax-check), and has been upfront when its sandbox
  can't install certain packages (no network for pip/model
  downloads) — in those cases it verifies logic with realistic
  stubs/mocks instead of assuming.
- I'm a backend/AI-leaning student, weak on frontend — keep frontend
  simple, explain decisions since I'm learning, don't over-engineer.
- I'm on Windows (Git Bash/MINGW64) — use `py`, not `python3`, in
  commands.
- We've been testing rigorously: I built ground-truth eval sets,
  questioned suspicious results (e.g., "why is BM25 scoring
  perfectly, that seems too good"), and Claude has caught its own
  bugs by testing before shipping rather than after I report them.

## Current status: Modules 1-4 complete, Module 5 in progress

**Module 1 (foundation):** Done. Repo structure, backend
(Node/Express, health check), ai-service (FastAPI, health check),
frontend (React/Vite, minimal), Docker Compose for all of it +
Postgres.

**Module 2 (ingestion):** Done. PDF → text extraction → cleaning →
metadata extraction → chunking, scoped to Supreme Court + Islamabad
High Court only (Balochistan/Peshawar explicitly excluded — Peshawar
merges many cases per PDF, out of scope). Real bugs found and fixed
during testing (page headers, footnote markers, sentence-splitter
fragmentation on abbreviations like "Mr."). Metadata extraction is
regex-based per-court and often only `partial` (not all fields
found) — decided this is fine; missing metadata will be filled in at
query time by an LLM reading the full source document (a Module 5
idea, not yet built).

**Module 3 (search infrastructure):** Done. Embeddings
(sentence-transformers), ChromaDB vector storage, semantic search,
BM25 keyword search, metadata filtering, a Recall@K/MRR evaluation
harness (`ai-service/eval/test_queries.json` +
`scripts/evaluate_retrieval.py`). Compared 3 embedding models:
`minilm` (general-purpose, kept), `legalbert` (raw BERT checkpoint,
DROPPED — underperformed due to a training-objective mismatch, not
a domain problem), `legalbert_st` (properly fine-tuned legal
sentence-transformer, kept — currently the strongest individual
retriever measured).

**Module 4 (hybrid retrieval + reranking):** Done, NOT YET
COMMITTED to git as of this handoff — check `git status` first
thing in the new chat. Built RRF-based hybrid retrieval
(`app/hybrid_search.py`), cross-encoder reranking
(`app/reranker.py`, `app/reranked_search.py`), new endpoints
`/search/hybrid` and `/search/reranked`. Key findings (all logged in
`docs/retrieval-notes.md`, Tests 1-9):
- Naive RRF fusion can *underperform* a strong standalone retriever
  (`legalbert_st` alone beat `hybrid+legalbert_st` on every metric)
  when one input method is much weaker on a given query type.
- A general-purpose reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`,
  MS MARCO-trained) actively HURT an exact-citation-lookup query
  (`"PLD 2024 SC 1276"`) — pushed the correct chunk from rank 4 to
  rank 11 — because it's not trained for exact-identifier matching.
  Confirmed via a purpose-built trace tool
  (`scripts/debug_query_trace.py`) that retrieval was NOT the
  problem, reranking specifically was.
- Conclusion: no single fixed method/pipeline wins for every query
  type (keyword lookups vs. paraphrased questions vs. citation
  lookups each favor different methods). This directly motivates
  Module 6 (query classification/routing), not yet built.

**Module 5 (RAG):** IN PROGRESS. Just started Session 5.1 (LLM
abstraction layer). Decided: Anthropic API (Claude), specifically
Claude Haiku for cost — `LLM_PROVIDER`/`LLM_MODEL_NAME`/`LLM_API_KEY`
env vars already exist. Just created `ai-service/app/llm.py` (a
`generate()` function wrapping the Anthropic SDK, provider-swappable
by design) and `app/config.py` was updated with LLM settings. THIS
WAS NOT FULLY TESTED OR CONFIRMED WORKING — my sandbox couldn't
install the `anthropic` package (no network access for pip installs,
confirmed directly despite it appearing in an "allowed domains"
list — actual proxy blocks it). Error-handling paths (missing API
key, unknown provider) need re-verification. Nothing from this
session has been packaged/delivered to the user yet.

## Known limitations, already documented (for the eventual README)

- Corpus: ~100 sample PDFs currently, real corpus is ~8,000 (SC +
  IHC only, by design).
- Metadata extraction is often partial (regex-based, court-specific).
- Retrieval quality varies significantly by query type (see Module 4
  findings above) — no single method/pipeline is best for everything.
- Reranker is a general-purpose model, not legal-domain-tuned.

## File structure

```
pakistan-legal-research/
├── frontend/        React (Vite) — minimal, just a backend health check page
├── backend/         Node/Express — minimal, just a health check
├── ingestion/        PDF processing pipeline (Module 2) — see ingestion/README.md
├── ai-service/       Python/FastAPI — embeddings, search, RAG (Modules 3-5)
│   ├── app/           importable modules (main.py is the entry point)
│   ├── scripts/         one-off scripts you run manually
│   └── eval/            ground-truth test set for retrieval evaluation
├── docs/
│   ├── docker.md
│   └── retrieval-notes.md   ALL the real findings/testing history — read this
├── docker-compose.yml
└── .env.example
```

Full ai-service file-by-file breakdown is in `ai-service/README.md`.

## Immediate next step when you resume

Finish testing Session 5.1's `app/llm.py`, then continue with
Session 5.2 (basic RAG pipeline). Module 4 also still needs
committing to git — do that first.
