import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Smart Campus Energy AI Dashboard",
  description:
    "AI-driven smart campus energy analytics, demand forecasting, anomaly detection, and energy conservation platform.",
  icons: {
    icon: "data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>⚡</text></svg>",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen text-slate-100 antialiased selection:bg-sky-500/30 selection:text-sky-200">
        {children}
      </body>
    </html>
  );
}
