/** Environment access (build-time NEXT_PUBLIC_* values only). */

const DEFAULT_API_URL = "http://localhost:8000";

export const env = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_URL,
  appName: "FasalRakshak",
  tagline: "Scan. Predict. Protect.",
} as const;