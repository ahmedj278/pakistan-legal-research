"""
Tests for app/evaluation.py's evaluate_rag() (Module 5, Session 5.6).
Ported from interactive testing done while building this module —
tests the METRIC computation logic itself against a fake answer_fn,
not a real LLM.
"""

from app.evaluation import evaluate_rag


def test_evaluate_rag_computes_grounded_and_citation_correctness_rates():
    test_queries = [
        {"query": "q1", "relevant_filenames": ["a.pdf"]},
        {"query": "q2", "relevant_filenames": ["b.pdf"]},
        {"query": "q3", "relevant_filenames": ["c.pdf"]},
        {"query": "q4", "relevant_filenames": ["d.pdf"]},
    ]

    def fake_answer_fn(query):
        return {
            "q1": {"grounded": True, "citations": [{"source_filename": "a.pdf"}]},          # correct + grounded
            "q2": {"grounded": True, "citations": [{"source_filename": "wrong.pdf"}]},        # grounded but WRONG source
            "q3": {"grounded": False, "citations": []},                                       # not grounded
            "q4": {"grounded": True, "citations": [{"source_filename": "wrong.pdf"}, {"source_filename": "d.pdf"}]},
        }[query]

    metrics = evaluate_rag(fake_answer_fn, test_queries)

    assert metrics["n_queries"] == 4
    assert metrics["grounded_rate"] == 0.75   # q1, q2, q4 grounded; q3 not
    assert metrics["correct_citation_rate"] == 0.5  # q1 and q4 cite a correct source; q2 and q3 don't
