// Centralizes every call to the backend behind one module, rather
// than scattering fetch(`${BACKEND_URL}/...`) calls across each
// page component. Every function here returns parsed JSON on
// success and throws an Error with a readable message on failure —
// callers decide how to show that (loading/error states are
// Session 7.6's job, not this module's).

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:4000";

async function request(path, options = {}) {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message = data?.error || data?.detail || `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data;
}

export function checkHealth() {
  return request("/health");
}

export function search({ query, nResults = 5, court, year, documentType }) {
  return request("/api/search", {
    method: "POST",
    body: JSON.stringify({
      query,
      n_results: nResults,
      court,
      year,
      document_type: documentType,
    }),
  });
}

export function ask({ query, nPassages = 5, court, year, documentType }) {
  return request("/api/ask", {
    method: "POST",
    body: JSON.stringify({
      query,
      n_passages: nPassages,
      court,
      year,
      document_type: documentType,
    }),
  });
}

export function getDocument(filename, court) {
  const params = court ? `?court=${encodeURIComponent(court)}` : "";
  return request(`/api/documents/${encodeURIComponent(filename)}${params}`);
}
