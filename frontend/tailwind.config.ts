import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Risk semantics used across farmer/officer surfaces (docs/14 §5).
        field: {
          50: "#f2f8f1",
          100: "#dcefd9",
          500: "#2f7d32",
          600: "#256b28",
          700: "#1d541f",
        },
        risk: {
          low: "#15803d",
          medium: "#b45309",
          high: "#c2410c",
          critical: "#b91c1c",
        },
      },
      fontSize: {
        base: ["1rem", "1.6"], // 16px base — low-literacy friendly (docs/14 §1)
      },
    },
  },
  plugins: [],
};

export default config;