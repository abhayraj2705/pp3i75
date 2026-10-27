import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, /api calls are forwarded to the FastAPI backend (localhost locally, "backend" in Docker).
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: { "/api": process.env.API_TARGET || "http://localhost:8000" },
  },
});
