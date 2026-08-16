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

