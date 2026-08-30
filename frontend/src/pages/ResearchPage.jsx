import { useState } from "react";
import { ask } from "../api/client";
import CitationCard from "../components/CitationCard";
import Spinner from "../components/Spinner";

function ResearchPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await ask({ query });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h1>Research Mode</h1>
      <p className="page-subtitle">
        Ask a legal research question. The answer is generated from retrieved judgments and
        cites its sources — always verify against the full judgment text before relying on it.
      </p>

      <form onSubmit={handleSubmit} className="search-form">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Can a wife get maintenance after khula?"
          aria-label="Research question"
        />
        <button type="submit" disabled={loading || !query.trim()}>
          Ask
        </button>
      </form>

      {/* RAG calls genuinely take several seconds (retrieval + a real
          LLM call) — a bare spinner with no context reads as "stuck"
          past a couple seconds, so this sets the expectation. */}
      {loading && <Spinner label="Generating an answer… this can take up to 15-20 seconds." />}

      {error && <p className="search-error">{error}</p>}

      {result && (
        <div className="research-result">
          <h2>Answer</h2>
          <p className="research-answer">{result.answer || "No answer was generated."}</p>

          {/* Session 5.5's grounded flag surfaced directly to the user:
              zero citations means either an honest "insufficient
              evidence" decline or an uncited answer — either way, the
              user should see this rather than trust an unsourced
              answer silently. See app/rag.py's docstring for the full
              reasoning on why this can't distinguish the two cases. */}
          {result.grounded === false && result.warning && (
            <div className="grounding-warning">{result.warning}</div>
          )}

          {result.citations && result.citations.length > 0 && (
            <>
              <h2>Sources</h2>
              <div className="search-results">
                {result.citations.map((citation) => (
                  <CitationCard key={citation.chunk_id} citation={citation} />
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}

export default ResearchPage;
