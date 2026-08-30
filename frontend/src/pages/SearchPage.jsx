import { useState } from "react";
import { search } from "../api/client";
import ResultCard from "../components/ResultCard";
import Spinner from "../components/Spinner";

// Known court slugs, confirmed directly against
// ingestion/src/config.py (not guessed) — update this list if a new
// court is added there.
const COURT_OPTIONS = [
  { value: "", label: "Any court" },
  { value: "supreme_court", label: "Supreme Court of Pakistan" },
  { value: "islamabad_high_court", label: "Islamabad High Court" },
];

// Confirmed against ingestion/src/metadata.py's detect_document_type().
// "UNKNOWN" is a fallback for failed detection, not a real category
// a user would search for, so it's deliberately left out here.
const DOCUMENT_TYPE_OPTIONS = [
  { value: "", label: "Any type" },
  { value: "JUDGMENT", label: "Judgment" },
  { value: "ORDER_SHEET", label: "Order Sheet" },
];

function SearchPage() {
  const [query, setQuery] = useState("");
  const [court, setCourt] = useState("");
  const [year, setYear] = useState("");
  const [documentType, setDocumentType] = useState("");

  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    // Cleared immediately, not just on error/success — otherwise a
    // new search visibly shows the PREVIOUS search's stale results
    // while the new one is still loading, which looks like the new
    // search already finished when it hasn't.
    setResults([]);

    try {
      const data = await search({
        query,
        court: court || undefined,
        year: year ? Number(year) : undefined,
        documentType: documentType || undefined,
      });
      setResults(data.results || []);
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
      setHasSearched(true);
    }
  }

  return (
    <section>
      <h1>Search Judgments</h1>

      <form onSubmit={handleSubmit} className="search-form">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. maintenance after khula, or PLD 2024 SC 1276"
          aria-label="Search query"
        />

        <div className="search-filters">
          <select value={court} onChange={(e) => setCourt(e.target.value)} aria-label="Court filter">
            {COURT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          <input
            type="number"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            placeholder="Year"
            aria-label="Year filter"
          />

          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            aria-label="Document type filter"
          >
            {DOCUMENT_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <button type="submit" disabled={loading || !query.trim()}>
          Search
        </button>
      </form>

      {loading && <Spinner label="Searching…" />}
      {error && <p className="search-error">{error}</p>}

      {!loading && !hasSearched && !error && (
        <p className="empty-state">
          Enter a query above to search Pakistani court judgments — try a topic
          ("maintenance after khula") or a citation ("PLD 2024 SC 1276").
        </p>
      )}

      {!loading && hasSearched && !error && results.length === 0 && (
        <p>No results found. Try a different query or fewer filters.</p>
      )}

      <div className="search-results">
        {results.map((result) => (
          <ResultCard key={result.chunk_id} result={result} />
        ))}
      </div>
    </section>
  );
}

export default SearchPage;
