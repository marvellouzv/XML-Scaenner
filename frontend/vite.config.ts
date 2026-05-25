import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backendPort = process.env.VITE_BACKEND_PORT ?? "8011";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5180,
    proxy: {
      "/api": {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true
      }
    }
  }
});
