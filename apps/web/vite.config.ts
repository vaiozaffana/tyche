import { cloudflare } from "@cloudflare/vite-plugin";
import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ command, mode }) => {
  if (command === "serve") {
    const env = loadEnv(mode, fileURLToPath(new URL("../..", import.meta.url)), "");
    if (env.GEMINI_API_KEY) process.env.GEMINI_API_KEY = env.GEMINI_API_KEY;
  }

  return {
    envDir: "../..",
    plugins: [
      ...(process.env.VITEST ? [] : [cloudflare()]),
      tanstackRouter({
        target: "react",
        autoCodeSplitting: true,
      }),
      react(),
      tailwindcss(),
    ],
  };
});
