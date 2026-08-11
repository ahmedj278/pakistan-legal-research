// Simple health check endpoint.
//
// Useful for: confirming the server is up, and later for Docker
// healthchecks / load balancer checks. Deliberately has zero
// dependencies on the database or AI service at this stage — this
// only proves the Express process itself is alive.

const express = require("express");

const router = express.Router();

router.get("/", (req, res) => {
  res.json({
    status: "ok",
    service: "backend",
    timestamp: new Date().toISOString(),
  });
});

module.exports = router;
