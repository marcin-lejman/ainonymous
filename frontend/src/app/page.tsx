"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchCases, deleteCase, CaseSummary } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function DashboardPage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchCases().then((c) => {
      setCases(c);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  async function handleDelete(id: string) {
    await deleteCase(id);
    setCases((prev) => prev.filter((c) => c.id !== id));
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">Twoje sprawy</h1>
          <p className="text-neutral-500 text-sm mt-1">
            Dokumenty przetworzone przez warstwę anonimizacji
          </p>
        </div>
        <Button onClick={() => router.push("/nowa")} size="lg">
          + Nowa sprawa
        </Button>
      </div>

      {loading ? (
        <div className="text-neutral-400 text-sm py-12 text-center">Wczytywanie...</div>
      ) : cases.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-16 h-16 rounded-2xl bg-neutral-100 flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">📄</span>
          </div>
          <h2 className="text-lg font-medium text-neutral-700 mb-2">Brak spraw</h2>
          <p className="text-neutral-400 text-sm max-w-sm mx-auto mb-6">
            Prześlij dokument, aby rozpocząć anonimizację. Wszystko odbywa się lokalnie na Twoim komputerze.
          </p>
          <Button onClick={() => router.push("/nowa")}>
            Rozpocznij pierwszą anonimizację
          </Button>
        </div>
      ) : (
        <div className="grid gap-3">
          {cases.map((c) => (
            <Card
              key={c.id}
              className="cursor-pointer hover:border-neutral-300 transition-colors"
              onClick={() => router.push(`/sprawa/${c.id}`)}
            >
              <CardHeader className="flex flex-row items-center justify-between py-4">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center shrink-0">
                    <span className="text-sm">📄</span>
                  </div>
                  <div>
                    <CardTitle className="text-[15px]">{c.name}</CardTitle>
                    <CardDescription className="text-xs mt-0.5">
                      {new Date(c.created_at).toLocaleDateString("pl-PL", {
                        day: "numeric",
                        month: "long",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                      {" · "}
                      {c.entity_count} encji
                      {c.has_pseudonymized && " · zanonimizowano"}
                    </CardDescription>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-neutral-400 hover:text-red-500 opacity-0 group-hover:opacity-100"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(c.id);
                  }}
                >
                  Usuń
                </Button>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
