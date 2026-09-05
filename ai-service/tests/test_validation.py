"""
Tests for the request validation added to app/main.py (Module 8).
Uses FastAPI's TestClient for real request/response cycles.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main


def _client():
    return TestClient(main.app)


def test_empty_query_rejected_with_400():
    resp = _client().post("/search", json={"query": "", "n_results": 5})
    assert resp.status_code in (400, 422)


def test_whitespace_only_query_rejected_with_400():
    # Passes pydantic's min_length=1 check (it's not an empty string)
    # but becomes "" after preprocess_query()'s cleanup — this is
    # exactly the case _clean_query_or_400() exists to catch.
    with patch.object(main, "semantic_search", return_value=[]):
        resp = _client().post("/search", json={"query": "   ", "n_results": 5})
    assert resp.status_code == 400


def test_n_results_above_upper_bound_rejected():
    resp = _client().post("/search", json={"query": "test", "n_results": 500})
    assert resp.status_code == 422


def test_n_results_below_lower_bound_rejected():
    resp = _client().post("/search", json={"query": "test", "n_results": 0})
    assert resp.status_code == 422


def test_n_results_within_bounds_accepted():
    with patch.object(main, "semantic_search", return_value=[]):
        resp = _client().post("/search", json={"query": "test", "n_results": 10})
    assert resp.status_code == 200


def test_unknown_court_value_rejected():
    resp = _client().post("/search", json={"query": "test", "court": "lahore_high_court"})
    # Not (yet) a real court slug in this project — see CourtSlug in
    # main.py. Should be a clear 422, not a silent zero-result search.
    assert resp.status_code == 422


def test_known_court_value_accepted():
    with patch.object(main, "semantic_search", return_value=[]):
        resp = _client().post("/search", json={"query": "test", "court": "supreme_court"})
    assert resp.status_code == 200


def test_year_before_pakistan_founding_rejected():
    resp = _client().post("/search", json={"query": "test", "year": 1900})
    assert resp.status_code == 422


def test_year_far_in_future_rejected():
    resp = _client().post("/search", json={"query": "test", "year": 3000})
    assert resp.status_code == 422


def test_ask_n_passages_above_upper_bound_rejected():
    resp = _client().post("/ask", json={"query": "test", "n_passages": 100})
    assert resp.status_code == 422


def test_search_expanded_n_variants_above_upper_bound_rejected():
    resp = _client().post(
        "/search/expanded", json={"query": "test", "n_results": 5, "n_variants": 50}
    )
    assert resp.status_code == 422


def test_unhandled_exception_returns_logged_500_not_raw_traceback():
    # raise_server_exceptions=False is needed here specifically: by
    # default TestClient re-raises exceptions (to make debugging
    # easier in tests) instead of routing them through the app's
    # registered exception handler the way a real server would.
    client = TestClient(main.app, raise_server_exceptions=False)
    with patch.object(main, "semantic_search", side_effect=RuntimeError("boom")):
        resp = client.post("/search", json={"query": "test"})
    assert resp.status_code == 500
    assert resp.json() == {"error": "Internal server error"}
