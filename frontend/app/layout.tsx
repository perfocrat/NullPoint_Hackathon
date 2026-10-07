import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "CareerLens | Career readiness, with evidence",
    template: "%s | CareerLens",
  },
  description:
    "Understand your career readiness with an evidence-led profile review, skill gaps, and a practical roadmap.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body>{children}</body>
    </html>
  );
}
