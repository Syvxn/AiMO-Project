import type { Metadata } from "next";
import { Space_Grotesk, Source_Serif_4, Goblin_One } from "next/font/google";
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

const goblinFont = Goblin_One({
  variable: "--font-goblin",
  subsets: ["latin"],
  weight: "400",
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
    <html lang="en" className={`${displayFont.variable} ${bodyFont.variable} ${goblinFont.variable} h-full antialiased`}>
      <body className="app-bg text-text-light">
        <AuthProvider>
          <div className="flex min-h-screen flex-col">
            <header className="border-b border-accent-orange/30 bg-gradient-to-r from-bg-dark to-bg-medium/80 backdrop-blur-md">
              <Navigation />
            </header>
            <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-6 sm:px-6 sm:py-8 xl:max-w-7xl xl:px-8 xl:py-10 min-[2200px]:max-w-[96rem] min-[2200px]:px-10 min-[2200px]:py-12">
              {children}
            </main>
            <footer className="mt-auto border-t border-accent-orange/20 bg-gradient-to-r from-bg-darkest to-bg-dark/90 px-4 py-3 text-[11px] text-text-beige sm:px-6 sm:py-4 sm:text-xs">
              <div className="mx-auto flex w-full max-w-6xl flex-col items-start justify-between gap-1 sm:flex-row sm:items-center xl:max-w-7xl min-[2200px]:max-w-[96rem]">
                <p>AiMO Website MVP</p>
              </div>
            </footer>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
