// Proxies full-document requests (Judgment Viewer, Session 7.4) to
// the AI service's GET /documents/{filename}. Same aiServiceUrl /
// fetch assumptions as routes/search.js — see that file's header.

const express = require("express");
const config = require("../config/env");

const router = express.Router();

const AI_SERVICE_URL = config.aiServiceUrl || "http://localhost:8000";

router.get("/:filename", async (req, res, next) => {
  try {
    const { filename } = req.params;
    const { court } = req.query;

    const url = new URL(`${AI_SERVICE_URL}/documents/${encodeURIComponent(filename)}`);
    if (court) url.searchParams.set("court", court);

    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({
        error: "AI service document request failed",
        detail: data,
      });
    }

    res.json(data);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
