// Proxies research-question requests to the AI service's RAG
// pipeline (Module 5). Same thin-passthrough reasoning as
// routes/search.js — see that file's header comment for the
// aiServiceUrl / fetch assumptions, which apply here identically.
//
// This can be a genuinely slow request (a real LLM call, plus
// retrieval) — no artificial timeout is added here beyond
// whatever Express/Node defaults apply, since cutting it short
// would just turn a slow-but-working answer into a failed one.

const express = require("express");
const config = require("../config/env");

const router = express.Router();

const AI_SERVICE_URL = config.aiServiceUrl || "http://localhost:8000";

router.post("/", async (req, res, next) => {
  try {
    const response = await fetch(`${AI_SERVICE_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body),
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({
        error: "AI service /ask request failed",
        detail: data,
      });
    }

    res.json(data);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
