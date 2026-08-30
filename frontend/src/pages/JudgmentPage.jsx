import { useEffect, useState } from "react";
import { useParams, useSearchParams, useLocation, Link } from "react-router-dom";
import { getDocument } from "../api/client";

const FULL_TEXT_PREVIEW_LENGTH = 2000;

function JudgmentPage() {
  const { filename } = useParams();
  const [searchParams] = useSearchParams();
  const court = searchParams.get("court") || undefined;
  const location = useLocation();

  // Present ONLY when arriving from a search result's "View full
  // judgment" link (see ResultCard.jsx) — a direct URL visit,
  // refresh, or bookmark has no originating query, so there's no
  // "relevant passage" to show. That's expected, not a bug.
  const relevantText = location.state?.relevantText;

  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showFullText, setShowFullText] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setShowFullText(false);

    getDocument(filename, court)
      .then(setDoc)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [filename, court]);

  if (loading) return <p>Loading judgment…</p>;

  if (error) {
    return (
      <section>
        <p className="search-error">{error}</p>
        <Link to="/">← Back to search</Link>
      </section>
    );
  }

  if (!doc) return null;

  const { metadata, text } = doc;
  const isLongText = text && text.length > FULL_TEXT_PREVIEW_LENGTH;
  const displayedText = showFullText || !isLongText ? text : text.slice(0, FULL_TEXT_PREVIEW_LENGTH) + "…";

  return (
    <section>
      <Link to="/" className="result-link">
        ← Back to search
      </Link>

      <h1>{metadata.case_title || "Untitled judgment"}</h1>

      <dl className="judgment-metadata">
        <dt>Court</dt>
        <dd>{metadata.court_name || "Unknown"}</dd>

        <dt>Year</dt>
        <dd>{metadata.year || "Unknown"}</dd>

        <dt>Case number</dt>
        <dd>{metadata.case_number || "Not available"}</dd>

        <dt>Citation</dt>
        <dd>{metadata.citation || "Not yet assigned"}</dd>

        <dt>Document type</dt>
        <dd>{metadata.document_type || "Unknown"}</dd>

        <dt>Judges</dt>
        <dd>{metadata.judges && metadata.judges.length > 0 ? metadata.judges.join(", ") : "Not available"}</dd>

        {metadata.hearing_date && (
          <>
            <dt>Hearing date</dt>
            <dd>{metadata.hearing_date}</dd>
          </>
        )}

        {metadata.decision_date && (
          <>
            <dt>Decision date</dt>
            <dd>{metadata.decision_date}</dd>
          </>
        )}
      </dl>

      {relevantText && (
        <div className="relevant-passage">
          <h2>Passage matching your search</h2>
          <p>{relevantText}</p>
        </div>
      )}

      <h2>Full document text</h2>
      <p className="judgment-text">{displayedText || "No text available for this document."}</p>

      {isLongText && (
        <button onClick={() => setShowFullText((prev) => !prev)} className="show-more-btn">
          {showFullText ? "Show less" : "Show full text"}
        </button>
      )}

      <div className="source-info">
        Source: {doc.filename} ({doc.court || "unknown court folder"})
      </div>
    </section>
  );
}

export default JudgmentPage;
