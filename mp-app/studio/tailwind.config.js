/** @type {import('tailwindcss').Config} */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { cwd } from "node:process";
import { fileURLToPath } from "node:url";

// Tailwind normally evaluates this from a file URL; Vitest transforms it to an HTTP URL.
const configDirectory = import.meta.url.startsWith("file:")
  ? dirname(fileURLToPath(import.meta.url))
  : cwd();
const designTokens = JSON.parse(
  readFileSync(resolve(configDirectory, "../shared/design-tokens.json"), "utf-8"),
);
const { color, typography, radius } = designTokens;
const primaryRgb = [0, 2, 4]
  .map((index) => parseInt(color.primary.slice(index + 1, index + 3), 16))
  .join(", ");

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: color.background,
        surface: color.surface,
        "brand-border": color.border,
        primary: {
          DEFAULT: color.primary,
          dark: color.primaryDark,
          light: color.primaryLight,
        },
        accent: {
          DEFAULT: color.accent,
          soft: color.accentSoft,
        },
        ink: {
          DEFAULT: color.textPrimary,
          dim: color.textSecondary,
        },
        success: color.primaryLight,
        danger: color.danger,
        warning: color.warning,
        info: color.info,
      },
      fontFamily: {
        vazir: typography.fontFamily.split(",").map((family) => family.trim()),
      },
      borderRadius: {
        card: `${radius.lg}px`,
      },
      boxShadow: {
        glow: `0 0 24px rgba(${primaryRgb}, 0.18)`,
        "glow-gold": "0 0 24px rgba(255, 215, 0, 0.16)",
        glass: "0 8px 32px rgba(2, 6, 12, 0.45)",
      },
      backgroundImage: {
        "emerald-radial":
          `radial-gradient(1200px 500px at 85% -10%, rgba(${primaryRgb}, 0.16), transparent 60%)`,
        "gold-radial":
          "radial-gradient(900px 420px at 10% 110%, rgba(255,215,0,0.10), transparent 55%)",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: 1 },
          "50%": { opacity: 0.55 },
        },
        "scan-line": {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
      },
      animation: {
        shimmer: "shimmer 1.6s linear infinite",
        "pulse-soft": "pulse-soft 2.4s ease-in-out infinite",
        "scan-line": "scan-line 2.8s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
