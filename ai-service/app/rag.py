"""
RAG pipeline (Module 5, Sessions 5.2-5.5).

Wires together retrieval (Module 4's full pipeline: BM25 + semantic
-> RRF -> rerank), the LLM (Session 5.1), and citation extraction
(Session 5.3) into one function: take a question, retrieve relevant
passages, ask the LLM to answer using ONLY those passages while
citing which passage number supports each claim, then parse those
citation markers into a structured, traceable source list.

Session 5.4 (grounded answer generation): reviewed and accepted as
already satisfied by the SYSTEM_PROMPT below (ONLY-use-passages
instruction + mandatory [N] citation format + explicit
no-fabrication instruction). Not re-engineered further — this is a
portfolio project, not a production legal system, and prompt-level
grounding is a reasonable, documented scope boundary rather than a
gap.

Session 5.5 (hallucination / insufficient-evidence safeguards): the
system prompt alone can't guarantee the LLM actually follows the
citation instruction. This module can't verify claim-level
correctness (that would need real NLI-style entailment checking,
out of scope here) — so instead it adds one honest, deterministic
signal: `grounded` is False whenever the LLM's answer contains zero
citation markers. This can't distinguish "the LLM correctly said
there wasn't enough evidence" from "the LLM answered anyway without
citing" — both produce zero citations — but flagging both for
manual review is strictly better than silently treating an uncited
answer as if it were fully sourced. Documented as a known
limitation, not something worth more engineering time here.

Session 6.3 (query routing): retrieval routes citation-lookup-shaped
queries (e.g. "PLD 2024 SC 1276") to hybrid_search directly, skipping
the reranker — see is_citation_lookup()'s docstring in
app/query_processing.py for the documented failure (docs/retrieval-
notes.md, Test 8) that justifies this specific, narrow routing rule.
"""

from app.reranked_search import reranked_search
from app.hybrid_search import hybrid_search
from app.llm import generate
from app.citations import build_citations
from app.query_processing import is_citation_lookup

import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a legal research assistant for Pakistani court judgments. "
    "Answer the user's question using ONLY the provided passages below. "
    "Do not use any outside knowledge. "
    "Cite your sources: whenever you state a fact or conclusion drawn "
    "from a passage, include its number in square brackets immediately "
    "after the claim, e.g. \"The court held that the appeal was allowed [2].\" "
    "Use the passage numbers exactly as given (e.g. [1], [2]) — never cite "
    "a passage number that was not provided to you. "
    "If the passages do not contain enough information to answer the "
    "question, say so plainly instead of guessing. Never invent a case "
    "name, citation, or fact that is not explicitly present in the "
    "passages. This is a research aid, not legal advice."
)


def build_context(passages: list) -> str:
    """
    Formats retrieved passages into a numbered block the LLM can
    reference, each labeled with enough metadata to be traceable
    back to its source document.
    """
    blocks = []
    for i, p in enumerate(passages, start=1):
        meta = p["metadata"]
        label = (
            f"[Passage {i}] "
            f"Court: {meta.get('court_name', 'Unknown')} | "
            f"Case: {meta.get('case_title') or meta.get('source_filename', 'Unknown')} | "
            f"Year: {meta.get('year', 'Unknown')}"
        )
        blocks.append(f"{label}\n{p['text']}")
    return "\n\n".join(blocks)


def answer_question(query_text: str, n_passages: int = 5, filters: dict = None) -> dict:
    # Session 6.3 routing: for a citation-shaped query, hybrid search's
    # own ranking is the better-performing deterministic choice (see
    # module docstring / is_citation_lookup()'s docstring for the
    # measured evidence) — skip the reranker rather than trust it here.
    if is_citation_lookup(query_text):
        passages = hybrid_search(query_text, n_results=n_passages, filters=filters)
    else:
        passages = reranked_search(query_text, n_results=n_passages, filters=filters)

    if not passages:
        # No point calling the LLM at all here — nothing to ground an
        # answer in, and every call costs real (if free-tier) quota.
        return {
            "query": query_text,
            "answer": (
                "I could not find any relevant passages in the corpus to "
                "answer this question."
            ),
            "passages": [],
            "citations": [],
            "grounded": False,
        }

    context = build_context(passages)
    prompt = f"Passages:\n\n{context}\n\nQuestion: {query_text}"

    answer_text = generate(prompt, system=SYSTEM_PROMPT, max_tokens=1024)
    citations = build_citations(answer_text, passages)

    # Deterministic hallucination/insufficient-evidence signal (Session
    # 5.5): passages were retrieved, but the LLM cited none of them in
    # its answer. See module docstring for why this one flag covers
    # both the "correctly declined" and "answered without grounding"
    # cases rather than trying to tell them apart.
    grounded = len(citations) > 0

    result = {
        "query": query_text,
        "answer": answer_text,
        "passages": passages,
        "citations": citations,
        "grounded": grounded,
    }

    if not grounded:
        logger.warning(f"Ungrounded answer for query={query_text!r} (zero citations)")
        result["warning"] = (
            "The model's answer did not cite any of the retrieved "
            "passages. This may mean it correctly identified "
            "insufficient evidence to answer, or it may have answered "
            "without proper grounding — review this answer manually "
            "before relying on it."
        )

    return result
