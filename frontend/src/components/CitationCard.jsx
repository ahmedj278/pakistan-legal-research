import { Link } from "react-router-dom";

// Shows one entry from answer_question()'s `citations` list — the
// shape confirmed directly against app/citations.py's build_citations()
// output: number, chunk_id, court_name, case_title, case_number,
// year, source_filename, text_snippet. Note there's no `court` slug
// here (unlike search results) — the Judgment link omits that query
// param, which is fine since get_document() scans all court folders
// when it's absent.
function CitationCard({ citation }) {
  const { number, case_title, court_name, case_number, year, source_filename, text_snippet } = citation;

  const judgmentLink = `/judgment/${encodeURIComponent(source_filename)}`;

  return (
    <article className="result-card">
      <div className="citation-number">[{number}]</div>
      <h3 className="result-title">{case_title || "Untitled judgment"}</h3>

      <div className="result-meta">
        <span>{court_name || "Unknown court"}</span>
        <span>{year || "Year unknown"}</span>
        <span>{case_number || "Case number not available"}</span>
      </div>

      <p className="result-excerpt">{text_snippet}</p>

      <Link to={judgmentLink} state={{ relevantText: text_snippet }} className="result-link">
        View full judgment →
      </Link>
    </article>
  );
}

export default CitationCard;
