# Frontend

React application (via Vite), for the Pakistan Legal Research
Platform.

**Status:** Minimal working page implemented (Module 1, Session
1.4). No search UI, routing, or real pages yet — just a page that
confirms it can reach the backend.

## Structure

```text
frontend/
├── index.html
├── vite.config.js
└── src/
    ├── main.jsx     mounts the React app
    ├── App.jsx       the (currently single) page component
    └── index.css     minimal global styles
```

## Why Vite (not Create React App)

Create React App is no longer actively maintained. Vite is the
current standard for new React projects: faster dev server, faster
builds, and simpler config. Since you're newer to frontend tooling,
it's also just fewer moving parts to reason about.

## Setup

```bash
cd frontend
npm install
```

## Run

```bash
npm run dev
```

Vite will print a local URL (typically `http://localhost:5173`).
Open it in a browser.

## What the page does

Not a static "Hello World" — it makes one real request: on load, it
calls the backend's `GET /health` endpoint and shows whether the
backend is reachable. That's a genuinely useful smoke test at this
stage, and it's the first real frontend↔backend wiring in the
project.

To see it actually turn green, the backend needs to be running too
(see `backend/README.md`):

```bash
# terminal 1
cd backend && npm run dev

# terminal 2
cd frontend && npm run dev
```

If the backend isn't running, the page will show `unreachable`
instead of `connected` — that's expected, not a bug.

## Notes

- `VITE_BACKEND_URL` (in the root `.env.example`) controls which
  backend URL it calls. Vite only exposes env vars prefixed with
  `VITE_` to browser code — anything without that prefix is
  invisible to the frontend by design (so backend secrets can't leak
  into client-side JavaScript).
- Kept intentionally simple: no router, no component library, no
  state management library. Those get added only when a real page
  (Module 7) actually needs them.
