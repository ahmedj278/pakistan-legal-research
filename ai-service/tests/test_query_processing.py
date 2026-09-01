"""
Tests for app/query_processing.py (Module 6, Sessions 6.1-6.3).
Ported from interactive testing done while building this module.
"""

import json
from pathlib import Path
from unittest.mock import patch

from app.query_processing import (
    preprocess_query,
    expand_query,
    multi_query_search,
    is_citation_lookup,
)


# --- Session 6.1: preprocess_query ------------------------------------

def test_preprocess_query_collapses_and_trims_whitespace():
    assert preprocess_query("  what   is\t\tkhula\n") == "what is khula"


def test_preprocess_query_normalizes_smart_quotes_and_dashes():
    assert preprocess_query("what\u2019s the rule \u2014 khula?") == "what's the rule - khula"


def test_preprocess_query_preserves_citation_formatting():
    assert preprocess_query("PLD 2024 SC 1276") == "PLD 2024 SC 1276"
    assert preprocess_query("S. 489-F PPC") == "S. 489-F PPC"


def test_preprocess_query_does_not_lowercase():
    assert preprocess_query("Khula and Maintenance") == "Khula and Maintenance"


def test_preprocess_query_handles_empty_and_none_input():
    assert preprocess_query("") == ""
    assert preprocess_query(None) == ""
    assert preprocess_query("   ") == ""


def test_preprocess_query_strips_wrapping_quotes():
    assert preprocess_query('"can a wife get maintenance after khula"') == "can a wife get maintenance after khula"


# --- Session 6.2: expand_query / multi_query_search --------------------

@patch("app.query_processing.generate")
def test_expand_query_returns_original_plus_variants(mock_generate):
    mock_generate.return_value = (
        "wife maintenance after khula\n"
        "post-khula maintenance rights\n"
        "maintenance following dissolution by khula"
    )
    variants = expand_query("Can a wife get maintenance after khula?", n_variants=3)
    assert variants[0] == "Can a wife get maintenance after khula?"
    assert len(variants) == 4


@patch("app.query_processing.generate")
def test_expand_query_dedupes_self_echoed_original(mock_generate):
    mock_generate.return_value = "Can a wife get maintenance after khula?\nmaintenance rights post-khula"
    variants = expand_query("Can a wife get maintenance after khula?", n_variants=3)
    assert variants.count("Can a wife get maintenance after khula?") == 1
    assert len(variants) == 2


@patch("app.query_processing.generate")
def test_expand_query_handles_empty_llm_response(mock_generate):
    mock_generate.return_value = ""
    assert expand_query("some query", n_variants=3) == ["some query"]


def test_multi_query_search_fuses_results_favoring_consistently_ranked_chunks():
    def fake_search_fn(query_text, n_results, **kwargs):
        data = {
            "original q": [{"chunk_id": "C1"}, {"chunk_id": "C2"}, {"chunk_id": "C3"}],
            "variant a": [{"chunk_id": "C2"}, {"chunk_id": "C1"}, {"chunk_id": "C4"}],
            "variant b": [{"chunk_id": "C1"}, {"chunk_id": "C5"}, {"chunk_id": "C2"}],
        }
        return data.get(query_text, [])

    with patch(
        "app.query_processing.expand_query",
        return_value=["original q", "variant a", "variant b"],
    ):
        fused = multi_query_search("original q", fake_search_fn, n_variants=2, n_results=5)
        fused_ids = [r["chunk_id"] for r in fused]
        assert fused_ids[0] == "C1"
        assert fused_ids[1] == "C2"


def test_multi_query_search_falls_back_to_original_query_if_expansion_fails():
    call_log = []

    def tracking_search_fn(query_text, n_results, **kwargs):
        call_log.append(query_text)
        return [{"chunk_id": "X1"}]

    with patch("app.query_processing.expand_query", side_effect=RuntimeError("LLM quota exceeded")):
        fused = multi_query_search("some query", tracking_search_fn, n_variants=3, n_results=5)
        assert call_log == ["some query"]
        assert [r["chunk_id"] for r in fused] == ["X1"]


# --- Session 6.3: is_citation_lookup ------------------------------------

def test_is_citation_lookup_detects_real_citation_formats():
    assert is_citation_lookup("PLD 2024 SC 1276") is True
    assert is_citation_lookup("2024 SCMR 1276") is True
    assert is_citation_lookup("PLJ 2019 Lahore 45") is True


def test_is_citation_lookup_false_on_real_eval_set_questions():
    eval_path = Path(__file__).resolve().parent.parent / "eval" / "test_queries.json"
    if not eval_path.exists():
        return  # eval set not present in this checkout; skip rather than fail
    with open(eval_path) as f:
        real_questions = [item["query"] for item in json.load(f)]
    false_positives = [q for q in real_questions if is_citation_lookup(q)]
    assert false_positives == []


def test_is_citation_lookup_rejects_adversarial_short_queries():
    # Common short words that could false-trigger a naive length/number check.
    assert is_citation_lookup("case number 1276 of 2024") is False
    assert is_citation_lookup("SC verdict on marriage act") is False
    assert is_citation_lookup("what is Section 489-F PPC") is False
    assert is_citation_lookup("khula 2024") is False
    assert is_citation_lookup("") is False
    assert is_citation_lookup("PLD") is False


def test_is_citation_lookup_documented_false_negative_on_lowercase():
    # Documented, accepted tradeoff — see is_citation_lookup()'s
    # docstring: false negatives (missed optimization) are the safe
    # failure direction, not false positives (degraded search).
    assert is_citation_lookup("pld 2024 sc 1276") is False
