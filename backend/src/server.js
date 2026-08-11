// Entry point: starts the HTTP server.
//
// Run with `npm run dev` (auto-restarts on file changes via
// nodemon) or `npm start` (plain node).

const createApp = require("./app");
const config = require("./config/env");

const app = createApp();

app.listen(config.port, () => {
  console.log(
    `[backend] listening on http://localhost:${config.port} (env: ${config.nodeEnv})`
  );
});
