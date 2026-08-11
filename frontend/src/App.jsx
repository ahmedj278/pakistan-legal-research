import { useEffect, useState } from "react";

// Falls back to localhost:4000 if VITE_BACKEND_URL isn't set, so the
// app still works immediately after `npm install && npm run dev`
// without requiring .env setup first.
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:4000";

function App() {
  // Rather than a static "Hello World" page, this does one small
  // real thing: confirms the frontend can actually reach the
  // backend. That's a genuinely useful smoke test at this stage of
  // the project, and it's the first piece of real frontend-backend
  // wiring the rest of the app will build on.
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    fetch(`${BACKEND_URL}/health`)
      .then((res) => {
        if (!res.ok) throw new Error(`Backend responded with ${res.status}`);
        return res.json();
      })
      .then(() => setStatus("connected"))
      .catch(() => setStatus("unreachable"));
  }, []);

  return (
    <main style={styles.main}>
      <h1>Pakistan Legal Research Platform</h1>
      <p style={styles.subtitle}>
        AI-powered research over Pakistani court judgments. Not legal
        advice.
      </p>
      <p style={styles.status}>
        Backend status:{" "}
        <strong style={{ color: statusColor(status) }}>{status}</strong>
      </p>
    </main>
  );
}

function statusColor(status) {
  if (status === "connected") return "#1a7f37";
  if (status === "unreachable") return "#c62828";
  return "#666";
}

const styles = {
  main: {
    fontFamily: "system-ui, sans-serif",
    maxWidth: "640px",
    margin: "4rem auto",
    padding: "0 1.5rem",
  },
  subtitle: {
    color: "#555",
  },
  status: {
    marginTop: "2rem",
    fontSize: "0.95rem",
  },
};

export default App;
