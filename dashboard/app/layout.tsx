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
  title: "AXIOM — Artificial Executive Operating System",
  description:
    "AI-native operating system. Boot. Coordinate. Execute. Evolve.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} dark`}
    >
      <body className="h-screen overflow-hidden bg-[var(--axiom-bg-base)] text-[var(--axiom-text-primary)] font-sans antialiased">
        {children}
      </body>
    </html>
  );
}