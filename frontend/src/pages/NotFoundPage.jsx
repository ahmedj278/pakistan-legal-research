import { Link } from "react-router-dom";

// Catch-all for any URL that doesn't match a real route — without
// this, react-router silently renders nothing, which looks like a
// broken app rather than a clear "page not found."
function NotFoundPage() {
  return (
    <section>
      <h1>Page not found</h1>
      <p>The page you're looking for doesn't exist.</p>
      <Link to="/">← Back to search</Link>
    </section>
  );
}

export default NotFoundPage;
