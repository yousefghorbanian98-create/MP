import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: false,
    allowedHosts: true,
    // M46-c5 — در dev هیچ پراکسی‌ای نبود، پس کلاینت به `/api/v1/...` می‌زد و
    // Vite همان مسیر را به index.html برمی‌گرداند؛ یعنی استودیو در dev هرگز
    // به بک‌اند نمی‌رسید. در production همین کار را nginx.conf می‌کند.
    proxy: {
      "/api": {
        target: process.env.MP_API_TARGET ?? "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/health": {
        target: process.env.MP_API_TARGET ?? "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: true,
  },
  build: {
    outDir: "dist",
    chunkSizeWarningLimit: 1200,
  },
});
