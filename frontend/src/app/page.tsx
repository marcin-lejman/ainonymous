"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchCases, deleteCase, CaseSummary } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchCases()
      .then((c) => {
        setCases(c);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  async function handleDelete(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    await deleteCase(id);
    setCases((prev) => prev.filter((c) => c.id !== id));
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Twoje dokumenty</h1>
          <p className="text-neutral-500 text-sm mt-1">
            Zanonimizowane dokumenty — wszystko przetworzone lokalnie
          </p>
        </div>
        <Button
          onClick={() => router.push("/nowa")}
          className="bg-gradient-to-r from-violet-500 to-indigo-600 hover:from-violet-600 hover:to-indigo-700 shadow-sm shadow-violet-200"
        >
          + Nowy dokument
        </Button>
      </div>

      {loading ? (
        <div className="text-neutral-400 text-sm py-12 text-center">
          Wczytywanie...
        </div>
      ) : cases.length === 0 ? (
        <div className="text-center py-24">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-100 to-indigo-100 flex items-center justify-center mx-auto mb-5">
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              className="text-violet-500"
            >
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-neutral-800 mb-2">
            Brak dokumentów
          </h2>
          <p className="text-neutral-500 text-sm max-w-sm mx-auto mb-8">
            Prześlij dokument, aby rozpocząć anonimizację.
            Cały proces odbywa się lokalnie — dane nie opuszczają Twojego komputera.
          </p>
          <Button
            onClick={() => router.push("/nowa")}
            size="lg"
            className="bg-gradient-to-r from-violet-500 to-indigo-600 hover:from-violet-600 hover:to-indigo-700 shadow-sm shadow-violet-200"
          >
            Rozpocznij pierwszą anonimizację
          </Button>
        </div>
      ) : (
        <div className="space-y-2">
          {cases.map((c) => (
            <div
              key={c.id}
              onClick={() => router.push(`/sprawa/${c.id}`)}
              className="group flex items-center justify-between bg-white rounded-xl border border-neutral-200/80 px-5 py-4 cursor-pointer hover:border-violet-200 hover:shadow-sm hover:shadow-violet-100/50 transition-all"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-violet-50 flex items-center justify-center shrink-0">
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-violet-500"
                  >
                    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                </div>
                <div>
                  <p className="font-medium text-[15px] text-neutral-900">
                    {c.name}
                  </p>
                  <p className="text-xs text-neutral-400 mt-0.5">
                    {new Date(c.created_at).toLocaleDateString("pl-PL", {
                      day: "numeric",
                      month: "long",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                    <span className="mx-1.5 text-neutral-300">·</span>
                    {c.entity_count === 1 ? "1 encja" : c.entity_count % 10 >= 2 && c.entity_count % 10 <= 4 && (c.entity_count % 100 < 12 || c.entity_count % 100 > 14) ? `${c.entity_count} encje` : `${c.entity_count} encji`}
                    {c.has_pseudonymized && (
                      <>
                        <span className="mx-1.5 text-neutral-300">·</span>
                        <span className="text-green-600">zanonimizowano</span>
                      </>
                    )}
                  </p>
                </div>
              </div>
              <button
                onClick={(e) => handleDelete(e, c.id)}
                className="px-3 py-1.5 text-xs text-neutral-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
              >
                Usuń
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
