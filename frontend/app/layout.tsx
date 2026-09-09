import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SOAR — Sovereign AI Workbench",
  description:
    "A sovereign on-premise AI workbench for research, analysis, creation, building and execution on your machine.",
  openGraph: {
    title: "SOAR — Sovereign AI Workbench",
    description:
      "A sovereign on-premise AI workbench for research, analysis, creation, building and execution on your machine.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} dark`}>
      <body className="min-h-screen bg-[#070A08] text-[#F1F5ED] antialiased selection:bg-[#B8F23D] selection:text-[#070A08]">
        {children}
      </body>
    </html>
  );
}
