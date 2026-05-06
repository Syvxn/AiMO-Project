import type { Metadata } from "next";
import { Space_Grotesk, Source_Serif_4 } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { Navigation } from "@/components/navigation";

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
      <body className="min-h-full app-bg text-natural-white">
        <AuthProvider>
          <header className="border-b border-accent-orange/30 bg-gradient-to-r from-bg-dark to-bg-medium/80 backdrop-blur-md">
            <Navigation />
          </header>
          <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-6 py-8">{children}</main>
          <footer className="border-t border-accent-orange/20 bg-gradient-to-r from-bg-darkest to-bg-dark/90 px-6 py-4 text-xs">
            <div className="mx-auto flex w-full max-w-6xl items-center justify-between">
              <p>AiMO Website MVP</p>
              <p>Open-source learning platform</p>
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
