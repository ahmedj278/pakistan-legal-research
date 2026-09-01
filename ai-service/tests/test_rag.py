"""
Tests for app/rag.py (Module 5, Sessions 5.2/5.5, Module 6 Session 6.3
routing). Ported from interactive testing done while building this
module — the LLM and retrieval calls are mocked throughout, since
these tests are about rag.py's own orchestration logic (routing,
grounding-flag computation, early-exit on empty retrieval), not about
real model output.
"""

from unittest.mock import patch

from app import rag

FAKE_PASSAGE = {
    "chunk_id": "c1",
    "text": "the court allowed the appeal",
    "metadata": {
        "court_name": "SC", "case_title": "A v B", "case_number": "1",
        "year": 2020, "source_filename": "a.pdf",
    },
}


# --- Session 5.5: grounded flag -----------------------------------------

def test_grounded_true_when_answer_cites_a_passage():
    with patch.object(rag, "reranked_search", return_value=[FAKE_PASSAGE]), \
         patch.object(rag, "generate", return_value="The appeal was allowed [1]."):
        result = rag.answer_question("some question")
    assert result["grounded"] is True
    assert "warning" not in result


def test_grounded_false_with_warning_when_answer_does_not_cite_anything():
    with patch.object(rag, "reranked_search", return_value=[FAKE_PASSAGE]), \
         patch.object(rag, "generate", return_value="The appeal was allowed."):
        result = rag.answer_question("some question")
    assert result["grounded"] is False
    assert "warning" in result


def test_grounded_false_when_model_honestly_declines():
    with patch.object(rag, "reranked_search", return_value=[FAKE_PASSAGE]), \
         patch.object(rag, "generate", return_value="The provided passages do not contain enough information."):
        result = rag.answer_question("some question")
    # Documented limitation: an honest decline and an uncited
    # hallucination look identical here (both zero citations) — see
    # rag.py's module docstring for why this is an accepted tradeoff.
    assert result["grounded"] is False


def test_no_llm_call_when_no_passages_retrieved():
    call_tracker = {"called": False}

    def fake_generate(*a, **kw):
        call_tracker["called"] = True
        return "should not happen"

    with patch.object(rag, "reranked_search", return_value=[]), \
         patch.object(rag, "generate", fake_generate):
        result = rag.answer_question("some question")

    assert result["grounded"] is False
    assert call_tracker["called"] is False


# --- Session 6.3: citation-lookup routing --------------------------------

def test_citation_shaped_query_routes_to_hybrid_search_not_reranked():
    with patch.object(rag, "hybrid_search", return_value=[FAKE_PASSAGE]) as mock_hybrid, \
         patch.object(rag, "reranked_search", return_value=[FAKE_PASSAGE]) as mock_reranked, \
         patch.object(rag, "generate", return_value="Answer [1]."):
        rag.answer_question("PLD 2024 SC 1276")

    assert mock_hybrid.called
    assert not mock_reranked.called


def test_ordinary_question_still_routes_to_reranked_search():
    with patch.object(rag, "hybrid_search", return_value=[FAKE_PASSAGE]) as mock_hybrid, \
         patch.object(rag, "reranked_search", return_value=[FAKE_PASSAGE]) as mock_reranked, \
         patch.object(rag, "generate", return_value="Answer [1]."):
        rag.answer_question("Can a wife get maintenance after khula?")

    assert mock_reranked.called
    assert not mock_hybrid.called
