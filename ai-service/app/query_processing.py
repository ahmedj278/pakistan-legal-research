"""
Query preprocessing and expansion (Module 6, Sessions 6.1-6.2).

Two deliberately separate concerns, kept in one file because they're
both "things done to a query before it reaches retrieval":

- preprocess_query() (6.1): deterministic, no LLM, runs on EVERY
  query, free and instant.
- expand_query() / multi_query_search() (6.2): uses the LLM, costs
  one extra API call per search — opt-in, not run automatically on
  every query. See app/main.py for where each is wired in.
"""

import re
import unicodedata

from app.llm import generate
from app.hybrid_search import reciprocal_rank_fusion

# ---------------------------------------------------------------------------
# Session 6.1 — query preprocessing
# ---------------------------------------------------------------------------

# Curly quotes and dashes commonly introduced by copy-pasting from
# Word/PDF sources or browser autocorrect. Normalized to their plain
# ASCII equivalents since they're visually identical to a user but
# can silently break exact-match keyword lookups (e.g. a citation
# copy-pasted with a curly quote in it).
_QUOTE_MAP = {
    "\u2018": "'", "\u2019": "'",  # curly single quotes
    "\u201c": '"', "\u201d": '"',  # curly double quotes
    "\u2013": "-", "\u2014": "-",  # en dash, em dash
}


def preprocess_query(query_text: str) -> str:
    """
    Deterministic cleanup applied to every incoming query before it
    reaches retrieval. Kept intentionally minimal (project's own
    instruction: don't add unnecessary complexity):

    - Collapses/trims whitespace (extra spaces/tabs/newlines from
      copy-paste don't affect meaning but can affect edge cases in
      tokenization).
    - Normalizes smart quotes/dashes to plain ASCII (see _QUOTE_MAP).
    - Strips a NARROW set of leading/trailing punctuation only (a
      trailing "?" or wrapping quotes) — never interior punctuation,
      since legal citations depend on it (e.g. "PLD 2024 SC 1276",
      "S. 489-F PPC").

    Deliberately does NOT lowercase the whole query: BM25's own
    tokenizer (app/bm25_search.py) already lowercases internally, so
    doing it again here would be redundant, not additive, and risks
    the two normalization steps silently diverging later if one
    changes without the other.

    Never raises on empty/whitespace-only input — returns "".
    """
    if not query_text:
        return ""

    text = unicodedata.normalize("NFKC", query_text)

    for smart, plain in _QUOTE_MAP.items():
        text = text.replace(smart, plain)

    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip(" ?!.,;:\"'")

    return text


# ---------------------------------------------------------------------------
# Session 6.2 — query expansion / reformulation
# ---------------------------------------------------------------------------

EXPANSION_SYSTEM_PROMPT = (
    "You rewrite legal research questions into alternative phrasings "
    "for a search engine, so the same underlying question can be "
    "matched even when a document uses different wording or legal "
    "terminology. Given the user's question, produce exactly {n} "
    "different rephrasings of it, each preserving the SAME meaning. "
    "Output ONLY the rephrasings, one per line. No numbering, no "
    "bullet points, no explanation, no repeating the original "
    "question verbatim."
)


def expand_query(query_text: str, n_variants: int = 3) -> list:
    """
    Uses the LLM to generate n_variants alternative phrasings of
    query_text (the "query rewriting" example from the project spec:
    e.g. "maintenance after khula" -> "wife's maintenance following
    khula", "post-khula maintenance", etc.).

    Returns a list that ALWAYS starts with the original query_text,
    followed by up to n_variants LLM-generated rephrasings. The
    original is never dropped or replaced — expansion supplements
    retrieval, it doesn't gate it on the LLM producing anything
    usable.

    Costs one real LLM API call. Does not catch its own exceptions —
    a network/rate-limit failure here should surface clearly rather
    than being silently swallowed; multi_query_search() below decides
    how to degrade when this fails, since that's the actual caller
    that knows it has a fallback available.
    """
    prompt = f'Question: "{query_text}"'
    system = EXPANSION_SYSTEM_PROMPT.format(n=n_variants)

    raw = generate(prompt, system=system, max_tokens=200)
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    # Defensive de-dup against the original (case-insensitive):
    # smaller/free-tier models sometimes echo the original question
    # back as one of the "variants" despite the instruction not to —
    # observed behavior, not hypothetical, so worth guarding here
    # rather than assuming the prompt alone is enough.
    seen = {query_text.strip().lower()}
    variants = []
    for line in lines:
        key = line.lower()
        if key not in seen:
            seen.add(key)
            variants.append(line)

    return [query_text] + variants[:n_variants]


def multi_query_search(
    query_text: str,
    search_fn,
    n_variants: int = 3,
    n_results: int = 5,
    **search_fn_kwargs,
) -> list:
    """
    Retrieves using the original query PLUS n_variants LLM-generated
    rephrasings, then fuses all the result lists with the SAME
    Reciprocal Rank Fusion already used to combine BM25+semantic in
    app/hybrid_search.py — reused rather than reimplemented, since
    RRF only reasons about rank position, not where a ranked list
    came from. Fusing across different query phrasings is the exact
    same math as fusing across different retrieval methods.

    search_fn: any Module 3/4 search function with the signature
    (query_text, n_results, ...) -> list of result dicts — e.g.
    semantic_search, hybrid_search, or reranked_search. Passed in
    rather than hardcoded so this layers on top of whichever
    retrieval method the caller wants expansion applied to.

    If expand_query() itself fails (LLM error, rate limit, etc.),
    falls back to searching with just the original query — expansion
    is a quality enhancement, not a hard dependency; retrieval should
    still work even when the LLM is unavailable or quota-limited.
    """
    try:
        queries = expand_query(query_text, n_variants=n_variants)
    except Exception:
        queries = [query_text]

    ranked_lists = [search_fn(q, n_results, **search_fn_kwargs) for q in queries]
    fused = reciprocal_rank_fusion(*ranked_lists)
    return fused[:n_results]


# ---------------------------------------------------------------------------
# Session 6.3 — query routing (built ONLY where directly justified by an
# actual measured failure, per the spec's own instruction: "do not add
# unnecessary agentic complexity; if an ordinary deterministic pipeline
# performs better, prefer it.")
# ---------------------------------------------------------------------------

_YEAR_RE = re.compile(r"^(18|19|20)\d{2}$")
_CITATION_LOOKUP_MAX_WORDS = 8


def is_citation_lookup(query_text: str) -> bool:
    """
    Deterministic (no LLM) detector for queries that are themselves a
    bare case-citation string (e.g. "PLD 2024 SC 1276"), as opposed
    to a natural-language legal question.

    Why this exists, concretely — not speculative: docs/retrieval-
    notes.md, Test 8, documented a real measured failure. For the
    citation query "PLD 2024 SC 1276", hybrid search (BM25 + semantic
    + RRF) correctly ranked the right chunk at #4/20. The
    cross-encoder reranker then made it WORSE — pushing it to #11/20,
    past several unrelated chunks. Skipping the reranker for this
    query shape and using hybrid_search's ranking directly is exactly
    the deterministic-pipeline choice the spec asks for.

    Deliberately does NOT attempt the full 4-way classification the
    spec mentions (general search / citation lookup / metadata filter
    / legal research question). Only citation-lookup has an actual
    measured failure behind it in this project — building detectors
    for the other 3 categories without similar evidence would be
    exactly the unnecessary complexity the spec warns against. If a
    similar concrete failure shows up for another query type later,
    extend this then — don't pre-build speculative categories now.

    Tuned to fail toward FALSE NEGATIVES over false positives: a real
    citation typed in lowercase ("pld 2024 sc 1276") won't be caught,
    and just goes through the normal (safe, default) reranked
    pipeline — a missed optimization, not a degraded result. A false
    POSITIVE would incorrectly skip reranking for an ordinary
    question, which IS the harmful direction — so this requires an
    uppercase, abbreviation-shaped token specifically (not just any
    short word), plus a year, plus a separate number, all within a
    short query — not any one of those alone.
    """
    tokens = query_text.split()
    if not tokens or len(tokens) > _CITATION_LOOKUP_MAX_WORDS:
        return False

    has_year = False
    has_abbrev = False
    has_number = False

    for tok in tokens:
        cleaned = tok.strip(".,;:")
        if not cleaned:
            continue
        if _YEAR_RE.match(cleaned):
            has_year = True
        elif cleaned.isdigit():
            has_number = True
        elif cleaned.isalpha() and cleaned.isupper() and 2 <= len(cleaned) <= 6:
            has_abbrev = True

    return has_year and has_abbrev and has_number
