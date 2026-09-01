"""
Integration-level tests for app/main.py's FastAPI endpoints, using
FastAPI's TestClient (real HTTP request/response cycle, in-process —
no server needs to be running). Ported from interactive testing done
while building these endpoints.
"""

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main, documents as docmod


def test_search_endpoint_preprocesses_query_before_calling_semantic_search():
    with patch.object(main, "semantic_search", return_value=[]) as mock_search:
        client = TestClient(main.app)
        resp = client.post("/search", json={"query": "  what\u2019s khula?  ", "n_results": 3})

    assert resp.status_code == 200
    called_query = mock_search.call_args[0][0]
    assert called_query == "what's khula"
    assert resp.json()["query"] == "what's khula"


def test_documents_endpoint_returns_200_with_correct_text(tmp_path):
    (tmp_path / "supreme_court").mkdir()
    fake_doc = {
        "filename": "c.a._106_k_2024.pdf", "court": "supreme_court",
        "court_name": "Supreme Court of Pakistan", "case_title": "Test Case",
        "case_number": None, "year": None, "judges": [], "document_type": "JUDGMENT",
        "citation": None, "hearing_date": None, "decision_date": None,
        "cleaned_text": "Full judgment text here.", "raw_text": "raw",
    }
    with open(tmp_path / "supreme_court" / "c.a._106_k_2024.pdf.json", "w") as f:
        json.dump(fake_doc, f)

    with patch.object(docmod, "PROCESSED_DATA_DIR", tmp_path):
        client = TestClient(main.app)
        resp = client.get("/documents/c.a._106_k_2024.pdf")

    assert resp.status_code == 200
    assert resp.json()["text"] == "Full judgment text here."


def test_documents_endpoint_returns_404_for_missing_document(tmp_path):
    with patch.object(docmod, "PROCESSED_DATA_DIR", tmp_path):
        client = TestClient(main.app)
        resp = client.get("/documents/nonexistent.pdf")

    assert resp.status_code == 404


def test_all_expected_routes_are_registered():
    routes = {r.path for r in main.app.routes if hasattr(r, "path")}
    for expected in ["/health", "/search", "/search/hybrid", "/search/reranked", "/search/expanded", "/ask"]:
        assert expected in routes
