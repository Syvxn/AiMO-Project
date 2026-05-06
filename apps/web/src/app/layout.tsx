import type { Metadata } from "next";
import { Space_Grotesk, Source_Serif_4 } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const displayFont = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
});

const bodyFont = Source_Serif_4({
  variable: "--font-body",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AiMO Website",
  description: "AiMO learning platform website and game launcher",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${displayFont.variable} ${bodyFont.variable} h-full antialiased`}
    >
      <body className="min-h-full app-bg text-slate-100">
        <header className="border-b border-white/15 bg-black/25 backdrop-blur-md">
          <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
            <Link href="/" className="font-display text-2xl tracking-tight">
              AiMO
            </Link>
            <div className="flex items-center gap-4 text-sm sm:gap-6">
              <Link href="/play">Play</Link>
              <Link href="/about">About</Link>
              <Link href="/contact">Contact</Link>
              <Link href="/login">Login</Link>
            </div>
          </nav>
        </header>
        <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-6 py-8">{children}</main>
        <footer className="border-t border-white/15 bg-black/30 px-6 py-4 text-xs text-slate-300">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between">
            <p>AiMO Website MVP</p>
            <p>Open-source learning platform</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
