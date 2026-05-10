import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "latin-ext"] });

export const metadata: Metadata = {
  title: "AInonymous — lokalna anonimizacja dokumentów",
  description: "Anonimizuj dokumenty prawne lokalnie, bez wysyłania danych w chmurę",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pl">
      <body className={`${inter.className} antialiased bg-neutral-50 min-h-screen flex flex-col`}>
        <header className="bg-white border-b border-neutral-200/80 shrink-0">
          <div className="max-w-7xl mx-auto px-6 py-3.5 flex items-center justify-between">
            <a href="/" className="flex items-center gap-3 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-sm shadow-violet-200">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M17 11h1a3 3 0 0 1 0 6h-1" />
                  <path d="M9 12v6" />
                  <path d="M13 12v6" />
                  <path d="M14 7.5c-1 0-1.44.5-3 .5s-2-.5-3-.5-1.72.5-2.5.5a2.5 2.5 0 0 1 0-5c.78 0 1.57.5 2.5.5S9.44 3 11 3s2 .5 3 .5 1.72-.5 2.5-.5a2.5 2.5 0 0 1 0 5c-.78 0-1.5-.5-2.5-.5Z" />
                  <path d="M5 11h1a3 3 0 0 1 0 6H5" />
                </svg>
              </div>
              <div className="flex items-baseline gap-1.5">
                <span className="font-bold text-neutral-900 text-[16px] tracking-tight group-hover:text-violet-700 transition-colors">
                  AInonymous
                </span>
                <span className="text-[11px] font-medium text-violet-500 bg-violet-50 px-1.5 py-0.5 rounded-full">
                  local
                </span>
              </div>
            </a>
            <nav className="flex items-center gap-1 text-sm">
              <a href="/" className="px-3 py-1.5 rounded-lg text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100 transition-colors">
                Dokumenty
              </a>
              <a href="/przywroc" className="px-3 py-1.5 rounded-lg text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100 transition-colors">
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
