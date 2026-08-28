// Proxies search requests to the Python AI service.
//
// Kept as a thin passthrough deliberately: the AI service already
// owns all retrieval logic (Modules 3-4) — this layer's only job is
// to sit between the frontend and that service per the documented
// architecture (see root README.md's "Planned architecture"
// diagram), not duplicate any retrieval logic here.
//
// Uses reranked_search on the AI service side by default (the best
// general-purpose retrieval method per Module 4's evaluation) —
// this route is for plain search, not RAG; use routes/ask.js for
// question-answering.
//
// ASSUMPTION (please verify): this expects config/env.js to export
// `aiServiceUrl`, reading AI_SERVICE_URL from .env — that variable
// already exists in .env.example, documented there as "used from
// Module 1, Session 1.2". If your config/env.js uses a different
// key name, either add `aiServiceUrl` there or rename the reference
// below to match.
//
// Uses Node's built-in global `fetch` (available Node 18+, no new
// dependency needed) — confirm your Node version supports this if
// requests fail with "fetch is not defined".

const express = require("express");
const config = require("../config/env");

const router = express.Router();

const AI_SERVICE_URL = config.aiServiceUrl || "http://localhost:8000";

router.post("/", async (req, res, next) => {
  try {
    const response = await fetch(`${AI_SERVICE_URL}/search/reranked`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body),
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({
        error: "AI service search request failed",
        detail: data,
      });
    }

    res.json(data);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
