import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "FasalRakshak — Scan. Predict. Protect.",
    template: "%s · FasalRakshak",
  },
  description:
    "AI-Powered Crop Health & Early Warning Platform (SIH26131). Evidence > Guess: scan, understand risk, act with verified guidance.",
  applicationName: "FasalRakshak",
  manifest: "/manifest.webmanifest",
  icons: { icon: "/icon.svg", apple: "/icon.svg" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#2f7d32",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white">{children}</body>
    </html>
  );
}