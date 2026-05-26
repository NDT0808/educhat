import { defineConfig, loadEnv } from "vite";
import path from "path";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  // Set the third parameter to '' to load all env vars regardless of the `VITE_` prefix.
  const env = loadEnv(mode, process.cwd(), "");
  const port = parseInt(env["VITE_PORT"] || "5188");
  // PRIORITIZE API_PROXY_TARGET for the proxy, fall back to VITE_API_BASE_URL (which might be empty for frontend)
  const apiTarget = env["API_PROXY_TARGET"] || env["VITE_API_BASE_URL"] || "http://100.64.0.25:8088";

  return {
    plugins: [
      react(),
    ],
    resolve: {
      alias: {
        // Alias @ to the src directory
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      host: true,
      port: port,
      // Using server host from environment variables
      allowedHosts: [env["VITE_SERVER_HOST"] || "localhost", "100.64.0.25"],
      proxy: {
        "/v1": {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  };
});
