import { useParams } from "react-router-dom";

// Full document view (metadata, full text, source info) lands here
// in Session 7.4, using getDocument() from ../api/client — that
// endpoint (backend /api/documents/:filename -> ai-service
// /documents/{filename}) is already built and tested. This stub
// just proves the :filename route param arrives correctly.

function JudgmentPage() {
  const { filename } = useParams();

  return (
    <section>
      <h1>Judgment Viewer</h1>
      <p>
        Full document view for <code>{filename}</code> will go here (Session 7.4).
      </p>
    </section>
  );
}

export default JudgmentPage;
