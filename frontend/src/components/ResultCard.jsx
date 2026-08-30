import { Link } from "react-router-dom";

// Truncates chunk text for a preview excerpt. Chunks can run over
// 1000 characters (seen directly in real search results during
// testing) — way too long for a result list.
function truncate(text, maxLength = 280) {
  if (!text || text.length <= maxLength) return text;
  return text.slice(0, maxLength).trimEnd() + "…";
}

// Shows the fields the spec asks for: case title, court, date/year,
// citation, relevance, relevant excerpt.
//
// KNOWN LIMITATION (documented, not silently worked around): chunk-
// level search results don't carry a `citation` field at all — only
// the full per-document metadata (app/documents.py) has that slot,
// and even there it's usually null, since Pakistani courts assign
// citations (e.g. "PLD 2024 SC 1276") AFTER publication, not at
// ingestion time (see ingestion/src/metadata.py's own comment on
// this). `case_number` is shown instead — it's a different, real
// field, not a citation, but it's what's actually available here.
//
// `relevance` (Score) is the AI service's raw `rerank_score` (a
// cross-encoder logit — not a bounded percentage) — displayed as
// what it is, not dressed up as a false-precision percentage.
function ResultCard({ result }) {
  const { metadata, text, rerank_score } = result;

  const caseTitle = metadata.case_title || "Untitled judgment";
  const courtName = metadata.court_name || "Unknown court";
  const year = metadata.year || "Year unknown";
  const caseNumber = metadata.case_number || "Case number not available";

  const judgmentLink = `/judgment/${encodeURIComponent(metadata.source_filename)}${
    metadata.court ? `?court=${encodeURIComponent(metadata.court)}` : ""
  }`;

  return (
    <article className="result-card">
      <h3 className="result-title">{caseTitle}</h3>

      <div className="result-meta">
        <span>{courtName}</span>
        <span>{year}</span>
        <span>{caseNumber}</span>
        {typeof rerank_score === "number" && (
          <span title="Cross-encoder relevance score (raw, not a percentage)">
            Score: {rerank_score.toFixed(2)}
          </span>
        )}
      </div>

      <p className="result-excerpt">{truncate(text)}</p>

      <Link to={judgmentLink} className="result-link">
        View full judgment →
      </Link>
    </article>
  );
}

export default ResultCard;
