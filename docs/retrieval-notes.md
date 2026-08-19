# Retrieval notes

Informal testing notes from manually querying the semantic search
endpoint (Module 3, Session 3.3) against the ~100-document sample
corpus. Kept here so this reasoning isn't lost before Module 4's
formal retrieval evaluation (Session 4.4), which can build on these
observations with a proper test set.

## Test 1 — "police promotion seniority dispute"

- Returned multiple relevant chunks: promotion, disciplinary
  proceedings, seniority.
- Similarity scores: ~0.49–0.53.
- Reads as a genuine match, not noise.

## Test 2 — "maintenance after khula"

- Returned unrelated KPK employee/regularization cases.
- Similarity scores: ~0.32–0.37 (notably lower than Test 1).
- **Likely explanation**: the ~100-document sample skews toward
  service/administrative law (both original samples were), so a
  family-law-specific term like "khula" may simply not be
  represented yet. Worth re-testing once the corpus is scaled up in
  Module 8.
- **Bigger takeaway**: this is a concrete, observed case of pure
  semantic search's known weakness. When no genuinely relevant
  document exists, embedding search doesn't fail cleanly — it drifts
  toward whatever's generically "legal-sounding" instead of
  returning nothing. A keyword search (BM25, Session 3.4) wouldn't
  have this failure mode: if the literal word "khula" exists in an
  indexed document, BM25 finds it directly. This is the practical
  justification for hybrid retrieval (Module 4), grounded in an
  actual observed failure rather than a general assumption.

## Test 3 — Known e-passport procurement judgment, paraphrased queries

- The known judgment was retrieved consistently across paraphrased
  versions of the query.
- Other frequently co-retrieved documents were manually checked and
  confirmed to be genuinely related, separate judgments — not
  duplicate chunks or a chunking bug.
- Good validation that semantic search is doing real work, not just
  returning noise that happens to look plausible.

## Test 4 — "khula" and "murder", BM25 vs. semantic head-to-head (100-doc corpus)

Direct comparison, both endpoints, same queries.

**"khula":** BM25 correctly returned `64137.pdf` at the top — chunk
explicitly discusses a suit for dissolution of marriage on the basis
of khula. Semantic search did NOT return that document at all;
instead returned other judgments, one (`64396.pdf`) with genuine
conceptual overlap (marital breakdown, wife leaving the matrimonial
home) but the rest largely unrelated. Confirms the Test 2 hypothesis
directly: BM25 finds it, semantic search misses it and surfaces
noise instead.

**"murder":** Both BM25 and semantic search correctly returned
`68800.pdf` first. Semantic search's remaining results were only
loosely related (banking liability, NAB proceedings) — similarity
alone doesn't guarantee legal relevance. **A real bug was found
here**: BM25's other results (`63646.pdf`, unrelated commercial
arbitration) had a score of 0.0 — it was padding out to the
requested result count with non-matches instead of returning fewer,
genuinely-matching results. Fixed in `bm25_search.py`:
`keyword_search()` now filters out any result with `score <= 0`
before taking the top N, so a query can legitimately return fewer
results than requested. Verified against real chunk data: a query
for "promotion" with `n_results=10` correctly returned only the 6
chunks that actually matched, and a nonsense query now returns an
empty list instead of fabricated results.

## Conclusion after round 2

- BM25 reliably finds exact terminology; semantic search finds
  conceptually related language even without the exact word, but
  with real noise mixed in — similarity score is not the same as
  legal relevance.
- Neither method should be judged as "accurate" in isolation yet —
  absence of a good result may just mean the corpus (still ~100
  docs) doesn't contain a good match, not that retrieval failed.
- This is direct, concrete motivation for hybrid retrieval +
  reranking (Module 4) — and the right next step is to test whether
  hybrid actually improves top-k quality, not to assume it will.

## Test 5 — Embedding model comparison, formal evaluation (Recall@K, MRR)

Manual single-query testing (Test 4) wasn't reliable enough to
compare embedding models properly — too few data points, and
"khula" specifically is a non-English legal term neither model was
trained on, so a bad result there could mean "worse model" or just
"underrepresented word," impossible to tell apart from one query.
Built a proper evaluation harness instead (`app/evaluation.py`,
`scripts/evaluate_retrieval.py`): Recall@1/3/5 and MRR against a
manually curated set of query → known-correct-document pairs.

Three models compared:

| Method       | Recall@1 | Recall@3 | Recall@5 | MRR  |
|--------------|----------|----------|----------|------|
| bm25         | 1.0      | 1.0      | 1.0      | 1.0  |
| minilm       | 0.9      | 1.0      | 1.0      | 0.95 |
| legalbert    | 0.6      | 0.7      | 0.7      | 0.65 |
| legalbert_st | 0.8      | 1.0      | 1.0      | 0.9  |

- **legalbert** = `nlpaueb/legal-bert-base-uncased`, a raw BERT
  checkpoint with no native sentence-embedding config —
  sentence-transformers automatically falls back to mean-pooling
  token embeddings for it.
- **legalbert_st** = `IoannisKat1/legal-bert-base-uncased-legal-matryoshka`,
  the same base legal-domain model, but actually fine-tuned as a
  sentence embedder (contrastive training on sentence pairs, not
  just an automatic pooling fallback).

**Finding:** raw `legalbert` clearly underperforms both general-purpose
MiniLM and the properly fine-tuned legal model. This matches the
historical reason Sentence-BERT was created in the first place — raw
BERT's mean-pooled embeddings were found (in the original 2019
Sentence-BERT paper) to perform *worse* than averaged GloVe vectors
on sentence-similarity tasks, because BERT's masked-word training
objective was never aimed at making similar/dissimilar sentence
pairs separate cleanly in vector space. `legalbert_st` closing most
of the gap to MiniLM (Recall@1 0.6→0.8, MRR 0.65→0.9) confirms this
was a training-objective mismatch, not evidence that legal-domain
training itself doesn't help.

**Decision:** dropped `legalbert` from `app/model_registry.py`,
kept `legalbert_st` alongside `minilm` for continued comparison.
Neither BM25 nor either embedding model was declared a final winner
— BM25's perfect score here is expected and partly an artifact of a
small, keyword-friendly test set; the real comparison this sets up
is for Module 4's hybrid retrieval + reranking evaluation, using
this exact same harness.

**Caveat:** the test set is still small. These numbers should be
treated as directional, not conclusive, until more ground-truth
queries are added (see `scripts/find_documents_containing.py`) and/or
the corpus is scaled up in Module 8.

## Test 6 — Test set correction, and hybrid retrieval's real value

The 10 queries used in Test 5 turned out to still share many exact
words with their source chunks, despite being LLM-"paraphrased" —
confirmed by building `scripts/inspect_query_overlap.py`, which
measures literal word overlap between each query and its correct
document directly, instead of trusting "paraphrased" as a label.
Regenerated the queries with an explicit instruction to avoid shared
keywords. Results changed completely:

| Method       | Recall@1 | Recall@3 | Recall@5 | MRR   |
|--------------|----------|----------|----------|-------|
| bm25         | 0.1      | 0.4      | 0.5      | 0.242 |
| minilm       | 0.4      | 0.5      | 0.6      | 0.475 |
| legalbert_st | 0.6      | 0.7      | 0.8      | 0.675 |
| hybrid (bug) | 0.4      | 0.5      | 0.6      | 0.470 |

BM25 collapsing (MRR 1.0 → 0.242) once queries stop sharing literal
words is the expected, correct behavior — confirms the earlier
perfect scores were a test-set artifact (see Test 5's caveat), not
real retrieval quality. `legalbert_st` is now clearly the strongest
individual method — the first real evidence the legal-domain
fine-tuning helps, now that the test actually requires semantic
understanding instead of keyword luck.

**Bug found:** the "hybrid" row above used `hybrid_search()`'s
default embedding model (MiniLM), not `legalbert_st` — so hybrid was
fusing a weak method (BM25, 0.242 MRR here) with a medium one
(MiniLM, 0.475), never actually tested with the strongest available
component. Fixed: `hybrid_search()` now accepts `model_name`/
`collection_name` overrides (same pattern as `semantic_search()`),
and `evaluate_retrieval.py` runs hybrid against **every** registered
embedding model, so the real question — does BM25 + the *best*
embedding model beat that model alone? — can actually be answered,
instead of only ever testing hybrid with a mediocre pairing.

Re-run `scripts/evaluate_retrieval.py` after this fix to see the
corrected `hybrid+minilm` and `hybrid+legalbert_st` rows.

## Test 7 — Hybrid does not beat the best individual model

With the fix applied and a further-refined (harder, lower-overlap)
query set:

| Method              | Recall@1 | Recall@3 | Recall@5 | MRR   |
|---------------------|----------|----------|----------|-------|
| bm25                | 0.1      | 0.4      | 0.5      | 0.242 |
| minilm              | 0.5      | 0.7      | 0.8      | 0.62  |
| legalbert_st         | 0.7      | 0.9      | 1.0      | 0.808 |
| hybrid+minilm        | 0.4      | 0.5      | 0.6      | 0.47  |
| hybrid+legalbert_st  | 0.5      | 0.8      | 1.0      | 0.667 |

**`legalbert_st` alone beats `hybrid+legalbert_st` on every metric
except a tied Recall@5.** This is a real, mechanistic finding, not
noise:

RRF treats every input ranking as equally trustworthy — it only
looks at rank *position*, never how good that ranking actually is.
On this query set BM25 is weak (MRR 0.242, by design — the queries
deliberately avoid shared keywords). When BM25 confidently places a
*wrong* document at its own #1, that document still earns a full
`1/(k+1)` RRF contribution — occasionally enough to outrank the
correct chunk that `legalbert_st` already had correctly at #1 but
which only gets credit from one source. This matches the data
exactly: Recall@5 held at 1.0 (nothing was lost from the merged
candidate pool), but Recall@1 dropped (BM25 noise displaced the
correct answer from the very top rank, not further down).

**Conclusion:** naive, unweighted RRF is not a free improvement — it
helps when both retrievers are reasonably competent and
complementary, and can actively hurt when one is clearly weaker on a
given query distribution. For this project, right now,
**`legalbert_st` alone is the strongest retriever measured**, and
hybrid fusion as currently implemented adds no value on top of it.

This directly motivates Session 4.3 (reranking) as a genuinely
different mechanism worth testing, rather than assuming it will
help either: a cross-encoder reranker *jointly* scores each
candidate against the query for actual relevance, rather than
blindly merging rank positions the way RRF does. The open question
to test next: can reranking the combined BM25+semantic candidate
pool recover — or beat — `legalbert_st` alone, by filtering out
BM25's noisy candidates through genuine relevance judgment instead
of naive rank fusion?



## Test 8 — Real citation-lookup query exposes a compound weakness

Query: `"PLD 2024 SC 1276"` via `/search/hybrid`. The chunk literally
containing that exact citation scored BM25's clear #1 (`bm25_score`
17.30, far above any other result) — BM25 worked correctly. But its
final `rrf_score` (0.01639 ≈ exactly `1/61`) shows it got **zero**
credit from semantic search — MiniLM didn't retrieve it at all.
Meanwhile an unrelated chunk citing different cases outranked it
overall, because BM25's simple tokenizer splits the citation into
independent words (`pld`, `2024`, `sc`, `1276`), so any
citation-dense chunk picks up partial credit on the common tokens
(`"PLD"`, `"SC"`) even without matching the specific number. RRF
then compounds this by crediting that chunk from both lists while
the truly correct one only had one weak-but-real signal. Motivates
Session 4.3 (reranking) as a direct fix: a cross-encoder judges each
candidate against the query directly, rather than trusting blind
rank fusion.

## Test 9 — Reranking is the actual cause of the citation-lookup failure, not retrieval

Traced Test 8's failure directly with `scripts/debug_query_trace.py`,
per the question "was the correct chunk even in the pre-rerank
candidate pool?":

```
Hybrid candidate pool size: 20
FOUND in hybrid pool at rank 4/20, rrf_score=0.01639
After reranking: rank 11/20, rerank_score=-4.9249
```

**Confirmed: retrieval was never the problem.** BM25+RRF correctly
surfaced the right chunk at rank 4/20. The cross-encoder reranker
then made it *worse* — pushing it from rank 4 to rank 11, past
several unrelated chunks scored higher (best: -0.316 vs the correct
chunk's -4.925).

**Root cause:** `cross-encoder/ms-marco-MiniLM-L-6-v2` is trained on
MS MARCO — natural-language Bing search queries matched to
natural-language answer passages. It has no training signal for
"does this passage contain this exact formal citation string" — a
structured identifier lookup is a fundamentally different task from
what it was trained to judge. Instead of rewarding the verbatim
match, it appears to score based on general topical/discourse
similarity, where other legal-sounding passages can outscore the
one containing the actual answer.

**Conclusion:** this is a real, documented limitation of using a
general-purpose reranker for citation-style queries specifically —
not a flaw in the retrieval pipeline itself (which worked correctly
up to this point). Reinforces the same conclusion as the
hybrid-vs-alone finding (Test 7): no single fixed method (or
fixed pipeline configuration) is best for every query type. This is
exactly what the roadmap's Module 6 (query classification/routing —
explicitly including "citation lookup" as a named query type) is
meant to solve: detect a citation-style query and route it to BM25
directly, skipping semantic search and reranking entirely for that
case, rather than forcing every query through the same pipeline.
