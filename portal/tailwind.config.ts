import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0b0f17",
        panel: "#121826",
        panelLight: "#1a2230",
        border: "#1f2a3b",
        accent: "#60a5fa",
        pass: "#22c55e",
        fail: "#ef4444",
        na: "#94a3b8",
      },
    },
  },
  plugins: [],
};

export default config;
