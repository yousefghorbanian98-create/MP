/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: "#0B0F14",
        surface: "#111827",
        primary: {
          DEFAULT: "#00B86A",
          dark: "#00995A",
          light: "#34D399",
        },
        accent: {
          DEFAULT: "#FFD700",
          soft: "#FDE68A",
        },
        ink: {
          DEFAULT: "#F3F6F8",
          dim: "#9CA3AF",
        },
        success: "#34D399",
        danger: "#F87171",
        warning: "#FBBF24",
        info: "#38BDF8",
      },
      fontFamily: {
        vazir: ["'Vazirmatn Variable'", "Vazirmatn", "system-ui", "sans-serif"],
      },
      borderRadius: {
        card: "16px",
      },
      boxShadow: {
        glow: "0 0 24px rgba(0, 184, 106, 0.18)",
        "glow-gold": "0 0 24px rgba(255, 215, 0, 0.16)",
        glass: "0 8px 32px rgba(2, 6, 12, 0.45)",
      },
      backgroundImage: {
        "emerald-radial":
          "radial-gradient(1200px 500px at 85% -10%, rgba(0,184,106,0.16), transparent 60%)",
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
