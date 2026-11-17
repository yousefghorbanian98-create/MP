import { createRequire } from "node:module";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// خواندن نسخه با require — import JSON در بعضی محیط‌های CI با
// resolveJsonModule کار نمی‌کند و build/test را می‌شکند.
const pkg = createRequire(import.meta.url)("./package.json") as { version: string };

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
