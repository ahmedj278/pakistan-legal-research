// Builds and configures the Express app.
//
// Kept separate from server.js on purpose: this file describes
// *what* the app does (middleware, routes), while server.js
// describes *how it runs* (which port, starting the listener).
// Splitting them makes the app importable in tests later without
// actually binding to a port.

const express = require("express");
const cors = require("cors");
const morgan = require("morgan");

const healthRouter = require("./routes/health");
const searchRouter = require("./routes/search");
const askRouter = require("./routes/ask");
const documentsRouter = require("./routes/documents");
const { errorHandler, notFoundHandler } = require("./middleware/errorHandler");

function createApp() {
  const app = express();

  // Request logging. `morgan("dev")` gives concise, colored logs
  // (method, path, status, response time) — good enough for
  // development. This can be swapped for a structured JSON logger
  // (e.g. pino) later without touching anything else, since it's
  // just one middleware line.
  app.use(morgan("dev"));

  app.use(cors());
  app.use(express.json());

  app.use("/health", healthRouter);
  app.use("/api/search", searchRouter);
  app.use("/api/ask", askRouter);
  app.use("/api/documents", documentsRouter);

  // Must come after all real routes: catches anything unmatched.
  app.use(notFoundHandler);

  // Must be the LAST app.use(): Express identifies error handlers
  // by their four-argument signature, and their position in the
  // middleware chain determines what they can catch.
  app.use(errorHandler);

  return app;
}

module.exports = createApp;
