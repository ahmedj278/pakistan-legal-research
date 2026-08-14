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

## Conclusion at this stage

Basic semantic search works as expected on relevant queries, and
fails in the expected, well-understood way (semantic drift, not
crash/garbage) on queries with no good match in the current small
sample. Real retrieval quality — especially recall on
underrepresented topics — can't be judged properly until the corpus
is scaled up and/or BM25 + hybrid retrieval (Module 4) are in place.
Formal evaluation with a real query/ground-truth set is Session 4.4.
