"""
Tests for app/citations.py (Module 5, Session 5.3).

Ported from the interactive testing done while building this module
— not new assertions, just made permanent instead of throwaway.
"""

from app.citations import extract_cited_numbers, build_citations


def test_extract_cited_numbers_dedupes_and_preserves_first_appearance_order():
    text = "The court held [2] that [1] and again [2]."
    assert extract_cited_numbers(text) == [2, 1]


def test_build_citations_maps_valid_numbers_and_skips_invalid_ones():
    passages = [
        {
            "chunk_id": "c1",
            "text": "passage one text here",
            "metadata": {
                "court_name": "SC", "case_title": "A v B", "case_number": "123",
                "year": 2020, "source_filename": "a.pdf",
            },
        },
        {
            "chunk_id": "c2",
            "text": "passage two text here",
            "metadata": {
                "court_name": "LHC", "case_title": "C v D", "case_number": "456",
                "year": 2021, "source_filename": "b.pdf",
            },
        },
    ]
    answer = "Fact one [1]. Fact two [2]. Bogus fact [7]. Repeat of fact one [1]."
    citations = build_citations(answer, passages)

    assert len(citations) == 2
    assert citations[0]["number"] == 1
    assert citations[0]["case_title"] == "A v B"
    assert citations[1]["number"] == 2
    assert citations[1]["case_title"] == "C v D"


def test_build_citations_returns_empty_list_when_no_markers_present():
    passages = [{"chunk_id": "c1", "text": "t", "metadata": {"source_filename": "a.pdf"}}]
    assert build_citations("No markers here at all.", passages) == []


def test_build_citations_handles_empty_passages_without_crashing():
    assert build_citations("Fact [1].", []) == []
