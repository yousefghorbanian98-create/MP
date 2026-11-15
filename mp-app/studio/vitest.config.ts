import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

import pkg from "./package.json";

export default defineConfig({
  plugins: [react()],
  // همان defineی که vite.config.ts تزریق می‌کند — وگرنه تست‌ها
  // به ReferenceError می‌خورند (یک بار همین شد).
  define: { __APP_VERSION__: JSON.stringify(pkg.version) },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["tests/**/*.test.{ts,tsx}"],
    css: false,
  },
});
