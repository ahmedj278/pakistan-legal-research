# Docker development environment

Implemented in Module 1, Session 1.5.

## What's here

- One `Dockerfile` per service (`backend/`, `ai-service/`,
  `frontend/`), each tuned for **development**, not production:
  they run `nodemon`/`uvicorn --reload`/Vite's dev server, not an
  optimized production build.
- A root `docker-compose.yml` that wires up all three services plus
  a `postgres` container.
- Bind mounts (`./backend:/app`, etc.) so editing code on your host
  machine is reflected inside the running container immediately —
  no rebuild needed for day-to-day development.

## Why one shared `.env` file

Every service already read from a repo-root `.env` (see
`backend/src/config/env.js` and `ai-service/app/config.py`).
`docker-compose.yml` continues that pattern with `env_file: .env`
on each service, instead of introducing Docker-specific
duplicate config.

## The `localhost` vs. service-name gotcha

This is the trickiest part of Dockerizing a multi-service app, so
it's worth explaining clearly:

- When a service runs **directly on your machine** (`npm run dev`
  outside Docker), it reaches Postgres or the AI service at
  `localhost:<port>`, because they're all just processes on the same
  machine.
- When services run **inside Docker Compose**, each container is a
  separate machine on Docker's internal network. `localhost` inside
  the `backend` container refers to the backend container itself —
  not Postgres. Containers must address each other by **service
  name** instead (e.g. `postgres`, `ai-service`).

That's why `docker-compose.yml` overrides `DATABASE_URL` and
`AI_SERVICE_URL` for the `backend` service specifically, pointing at
`postgres` and `ai-service` instead of `localhost` — while `.env`
itself keeps the `localhost`-based values, which stay correct for
running services directly on your host.

The one exception is `VITE_BACKEND_URL` for the frontend: that value
is used by code running **in the browser**, which is not inside
Docker's network at all, so it correctly stays `localhost:4000`
even in the Docker Compose setup.

## `depends_on` and health checks

`backend` and `ai-service` both wait for Postgres via
`depends_on: postgres: condition: service_healthy`, using Postgres's
built-in `pg_isready` check. This avoids the classic "backend
crashes because it started before the database was ready" race
condition — even though nothing queries Postgres yet (that starts
in Module 2), it's set up correctly now so it doesn't need
revisiting later.

## What's deliberately not here yet

- No production/multi-stage Dockerfiles (Module 8).
- No Postgres schema, migrations, or actual queries (Module 2).
- No CI pipeline running these containers (Module 8).
