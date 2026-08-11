// Centralizes access to environment variables.
//
// Why this file exists: instead of scattering `process.env.X` calls
// throughout the codebase, every other module imports `config` from
// here. That gives us one place to see everything the backend
// depends on, and one place to set defaults or add validation later.
//
// The project uses a single .env file at the repo root (shared by
// backend, ai-service, etc.), so we point dotenv at that instead of
// backend/.env.

const path = require("path");
const dotenv = require("dotenv");

dotenv.config({ path: path.resolve(__dirname, "../../../.env") });

const config = {
  nodeEnv: process.env.NODE_ENV || "development",
  port: parseInt(process.env.BACKEND_PORT, 10) || 4000,
  aiServiceUrl: process.env.AI_SERVICE_URL || "http://localhost:8000",
};

module.exports = config;
