// Central error-handling middleware.
//
// Express recognizes this as an error handler specifically because
// it takes FOUR arguments (err, req, res, next). Any route that
// calls `next(err)`, or throws inside an async handler wrapped
// properly, ends up here instead of crashing the process or
// silently failing.
//
// This is intentionally simple for now: log it, return a generic
// JSON error. As real routes are added in later sessions, this can
// be extended to distinguish error types (validation errors vs.
// not-found vs. upstream AI-service failures, etc.).

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
  console.error(`[error] ${req.method} ${req.originalUrl} -`, err);

  const status = err.status || 500;
  res.status(status).json({
    error: {
      message: err.message || "Internal server error",
    },
  });
}

function notFoundHandler(req, res) {
  res.status(404).json({
    error: {
      message: `Route not found: ${req.method} ${req.originalUrl}`,
    },
  });
}

module.exports = { errorHandler, notFoundHandler };
