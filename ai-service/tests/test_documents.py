"""
Tests for app/documents.py (Module 7 prerequisite — full judgment
text for the Judgment Viewer). Ported from interactive testing done
while building this module.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app import documents as docmod

FAKE_DOC = {
    "filename": "c.a._106_k_2024.pdf",
    "court": "supreme_court",
    "court_name": "Supreme Court of Pakistan",
    "case_title": "Petitioners vs Azhar Ali (C.A. 106-K/24)",
    "case_number": None,
    "year": None,
    "judges": ["Justice Muhammad Ali Mazhar"],
    "document_type": "JUDGMENT",
    "citation": None,
    "hearing_date": "01.01.2024",
    "decision_date": "02.01.2024",
    "cleaned_text": "This is the full cleaned judgment text.",
    "raw_text": "RAW noisy text.",
}


@pytest.fixture
def fake_processed_dir(tmp_path):
    (tmp_path / "supreme_court").mkdir()
    (tmp_path / "islamabad_high_court").mkdir()
    with open(tmp_path / "supreme_court" / "c.a._106_k_2024.pdf.json", "w") as f:
        json.dump(FAKE_DOC, f)
    return tmp_path


def test_get_document_found_with_court_specified_prefers_cleaned_text(fake_processed_dir):
    with patch.object(docmod, "PROCESSED_DATA_DIR", fake_processed_dir):
        doc = docmod.get_document("c.a._106_k_2024.pdf", court="supreme_court")
    assert doc is not None
    assert doc["text"] == "This is the full cleaned judgment text."
    assert doc["metadata"]["case_title"] == "Petitioners vs Azhar Ali (C.A. 106-K/24)"


def test_get_document_found_via_scan_when_court_omitted(fake_processed_dir):
    with patch.object(docmod, "PROCESSED_DATA_DIR", fake_processed_dir):
        doc = docmod.get_document("c.a._106_k_2024.pdf")
    assert doc is not None
    assert doc["court"] == "supreme_court"


def test_get_document_returns_none_for_missing_document(fake_processed_dir):
    with patch.object(docmod, "PROCESSED_DATA_DIR", fake_processed_dir):
        assert docmod.get_document("nonexistent.pdf") is None


def test_get_document_returns_none_when_wrong_court_specified(fake_processed_dir):
    # Should NOT silently fall back to scanning other court folders.
    with patch.object(docmod, "PROCESSED_DATA_DIR", fake_processed_dir):
        assert docmod.get_document("c.a._106_k_2024.pdf", court="islamabad_high_court") is None


def test_get_document_returns_none_when_processed_dir_missing():
    with patch.object(docmod, "PROCESSED_DATA_DIR", Path("/nonexistent/path/xyz")):
        assert docmod.get_document("anything.pdf") is None
