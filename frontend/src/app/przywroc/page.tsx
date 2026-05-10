"use client";

import { useState, useEffect } from "react";
import { fetchCases, restoreText, CaseSummary } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";

export default function PrzywrocPage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [selectedCase, setSelectedCase] = useState("");
  const [inputText, setInputText] = useState("");
  const [restoredText, setRestoredText] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchCases().then((c) => {
      const withMapping = c.filter((cs) => cs.has_pseudonymized);
      setCases(withMapping);
      if (withMapping.length > 0) setSelectedCase(withMapping[0].id);
    });
  }, []);

  async function handleRestore() {
    if (!selectedCase || !inputText.trim()) return;
    setLoading(true);
    const result = await restoreText(selectedCase, inputText);
    setRestoredText(result.restored_text);
    setLoading(false);
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(restoredText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-neutral-900">Przywróć dane</h1>
        <p className="text-neutral-500 text-sm mt-1">
          Wklej odpowiedź z Claude, aby podmienić pseudonimy na prawdziwe dane
        </p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1.5">
            Sprawa
          </label>
          {cases.length === 0 ? (
            <p className="text-sm text-neutral-400">
              Brak dokumentów z zapisanym mapowaniem. Najpierw zanonimizuj dokument.
            </p>
          ) : (
            <select
              value={selectedCase}
              onChange={(e) => setSelectedCase(e.target.value)}
              className="h-9 w-full px-3 rounded-md border border-neutral-200 text-sm bg-white"
            >
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({new Date(c.created_at).toLocaleDateString("pl-PL")})
                </option>
              ))}
            </select>
          )}
          <p className="text-xs text-neutral-400 mt-1">
            Wybierz sprawę, z której pochodzi mapowanie pseudonimów
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1.5">
            Tekst z pseudonimami
          </label>
          <Textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Wklej tutaj odpowiedź z Claude zawierającą [PERSON_1], [LOCATION_2] itp."
            className="min-h-[200px] font-mono text-sm"
          />
        </div>

        <Button
          onClick={handleRestore}
          size="lg"
          className="w-full"
          disabled={!selectedCase || !inputText.trim() || loading}
        >
          {loading ? "Przywracam..." : "Przywróć oryginalne dane"}
        </Button>

        {restoredText && (
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-neutral-700">
                Tekst z przywróconymi danymi
              </h3>
              <Button variant="outline" size="sm" onClick={handleCopy}>
                {copied ? "Skopiowano!" : "Kopiuj"}
              </Button>
            </div>
            <Textarea
              value={restoredText}
              readOnly
              className="min-h-[200px] font-mono text-sm bg-neutral-50"
            />
          </Card>
        )}
      </div>
    </div>
  );
}
