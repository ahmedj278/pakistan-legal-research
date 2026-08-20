"""
Citation/source representation (Module 5, Session 5.3).

Extracts which passages the LLM actually cited in its answer text
(via [N] markers), and builds a structured citation list mapping
each cited number back to full source metadata — so the answer can
be displayed alongside a real, traceable "Sources" list, rather than
just a flat dump of every retrieved passage regardless of whether it
was actually used to support the answer.
"""

import re


def extract_cited_numbers(answer_text: str) -> list:
    """
    Finds citation markers like [1], [2] in the answer text. Returns
    the unique numbers cited, in order of first appearance (not
    sorted — first-appearance order matches how a reader encounters
    them in the answer).
    """
    matches = re.findall(r"\[(\d+)\]", answer_text)
    seen = []
    for m in matches:
        n = int(m)
        if n not in seen:
            seen.append(n)
    return seen


def build_citations(answer_text: str, passages: list) -> list:
    """
    Builds a structured citation list: for each passage number the
    LLM actually referenced in the answer text, attaches its real
    source metadata.

    Out-of-range citation numbers (the LLM citing a passage that
    doesn't exist — e.g. [7] when only 5 passages were provided) are
    silently skipped, never fabricated. This can happen despite the
    system prompt instructing against it; skipping rather than
    guessing keeps the citation list itself trustworthy even if the
    LLM's citation behavior isn't perfect.
    """
    cited_numbers = extract_cited_numbers(answer_text)
    citations = []

    for n in cited_numbers:
        index = n - 1  # passages are 1-indexed in the prompt/answer
        if index < 0 or index >= len(passages):
            continue

        passage = passages[index]
        meta = passage["metadata"]
        citations.append(
            {
                "number": n,
                "chunk_id": passage["chunk_id"],
                "court_name": meta.get("court_name"),
                "case_title": meta.get("case_title"),
                "case_number": meta.get("case_number"),
                "year": meta.get("year"),
                "source_filename": meta.get("source_filename"),
                "text_snippet": passage["text"][:300],
            }
        )

    return citations
