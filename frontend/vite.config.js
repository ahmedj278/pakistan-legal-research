import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// envDir points Vite at the repo-root .env instead of expecting
// frontend/.env, so frontend, backend, and ai-service all keep
// reading from the same single .env file (see .env.example).
export default defineConfig({
  plugins: [react()],
  envDir: "../",
});
