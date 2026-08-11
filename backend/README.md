# Backend

Node.js / Express application.

**Status:** Minimal skeleton implemented (Module 1, Session 1.2).
No real application routes yet — just app setup, config loading,
error handling, and a health check.

## Structure

```text
backend/
├── package.json
└── src/
    ├── server.js              entry point: starts the HTTP listener
    ├── app.js                 builds the Express app (middleware + routes)
    ├── config/
    │   └── env.js              centralized environment variable access
    ├── middleware/
    │   └── errorHandler.js     error handler + 404 handler
    └── routes/
        └── health.js           GET /health
```

## Setup

```bash
cd backend
npm install
```

## Run

```bash
npm run dev     # auto-restarts on file changes (nodemon)
# or
npm start       # plain node, no auto-restart
```

## Test it

```bash
curl http://localhost:4000/health
```

Expected response:

```json
{ "status": "ok", "service": "backend", "timestamp": "..." }
```

## Notes

- Reads configuration from the **root** `.env` file (not
  `backend/.env`) — see `src/config/env.js`. This keeps one shared
  env file for the whole project instead of duplicating variables
  across services.
- `AI_SERVICE_URL` is already loaded into config, but nothing calls
  the AI service yet — that starts once the AI service itself exists
  and is wired up in a later session.
