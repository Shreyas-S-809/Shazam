import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          green: "#1DB954",
          "green-light": "#1ed760",
          dark: "#0a0a0a",
          darker: "#050505",
          card: "#111111",
          border: "rgba(255,255,255,0.08)",
        },
        accent: {
          indigo: "#6366f1",
          purple: "#a855f7",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      backdropBlur: {
        glass: "20px",
      },
      animation: {
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "wave-bounce": "waveBounce 1.2s ease-in-out infinite",
      },
      keyframes: {
        waveBounce: {
          "0%, 100%": { transform: "scaleY(0.3)" },
          "50%": { transform: "scaleY(1)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
