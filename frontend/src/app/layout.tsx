import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "latin-ext"] });

export const metadata: Metadata = {
  title: "Warstwa Anonimizacji",
  description: "Lokalna anonimizacja dokumentów prawnych",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pl">
      <body className={`${inter.className} antialiased bg-white min-h-screen flex flex-col`}>
        <header className="border-b border-neutral-100 shrink-0">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-neutral-900 flex items-center justify-center">
                <span className="text-white text-sm font-bold">A</span>
              </div>
              <div>
                <span className="font-semibold text-neutral-900 text-[15px]">
                  Warstwa Anonimizacji
                </span>
                <span className="text-neutral-400 text-xs ml-2">lokalna</span>
              </div>
            </a>
            <nav className="flex items-center gap-6 text-sm">
              <a href="/" className="text-neutral-500 hover:text-neutral-900 transition-colors">
                Sprawy
              </a>
              <a href="/przywroc" className="text-neutral-500 hover:text-neutral-900 transition-colors">
                Przywróć dane
              </a>
            </nav>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full">
          {children}
        </main>
      </body>
    </html>
  );
}
