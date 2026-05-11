"use client";

import { useState, useEffect, useRef } from "react";
import { fetchCases, fetchCase, restoreText, CaseSummary } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { RestorePanel } from "@/components/RestorePanel";

export default function PrzywrocPage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [selectedCase, setSelectedCase] = useState("");
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [inputText, setInputText] = useState("");
  const [restoredText, setRestoredText] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchCases().then((c) => {
      const withMapping = c.filter((cs) => cs.has_pseudonymized);
      setCases(withMapping);
      if (withMapping.length > 0) {
        setSelectedCase(withMapping[0].id);
        loadMapping(withMapping[0].id);
      }
    });
  }, []);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (exportMenuRef.current && !exportMenuRef.current.contains(e.target as Node)) {
        setShowExportMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function loadMapping(caseId: string) {
    const data = await fetchCase(caseId);
    if (data.mapping?.reverse) {
      setMapping(data.mapping.reverse);
    }
  }

  async function handleCaseChange(caseId: string) {
    setSelectedCase(caseId);
    setRestoredText("");
    await loadMapping(caseId);
  }

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
    setShowExportMenu(false);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    const blob = new Blob([restoredText], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "przywrocone_dane.txt";
    a.click();
    URL.revokeObjectURL(url);
    setShowExportMenu(false);
  }

  const hasDocuments = cases.length > 0;

  return (
    <div className={restoredText ? "max-w-7xl mx-auto" : "max-w-2xl mx-auto"}>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Przywróć dane</h1>
          {!restoredText && (
            <p className="text-neutral-500 text-sm mt-1">
              Wklej odpowiedź z AI — pseudonimy zostaną zamienione na prawdziwe dane
            </p>
          )}
          {restoredText && (
            <p className="text-green-600 text-sm mt-1">
              Dane przywrócone — użyj &quot;Eksportuj&quot;, aby skopiować lub pobrać
            </p>
          )}
        </div>
        {restoredText && (
          <div className="relative" ref={exportMenuRef}>
            <Button
              onClick={() => setShowExportMenu((v) => !v)}
              className="bg-gradient-to-r from-violet-500 to-indigo-600 hover:from-violet-600 hover:to-indigo-700 shadow-sm shadow-violet-200"
            >
              {copied ? "✓ Skopiowano" : "Eksportuj ▾"}
            </Button>
            {showExportMenu && (
              <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-lg shadow-neutral-200/50 border border-neutral-200 p-1.5 z-50">
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-3 w-full px-3 py-2.5 text-sm text-left rounded-lg hover:bg-neutral-50 transition-colors"
                >
                  <span className="text-base">📋</span>
                  <div>
                    <p className="font-medium text-neutral-800">Kopiuj do schowka</p>
                    <p className="text-[11px] text-neutral-400">Z przywróconymi danymi</p>
                  </div>
                </button>
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-3 w-full px-3 py-2.5 text-sm text-left rounded-lg hover:bg-neutral-50 transition-colors"
                >
                  <span className="text-base">📄</span>
                  <div>
                    <p className="font-medium text-neutral-800">Pobierz jako .txt</p>
                    <p className="text-[11px] text-neutral-400">Zapisz plik z prawdziwymi danymi</p>
                  </div>
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {!hasDocuments ? (
        <Card className="p-8 text-center">
          <div className="w-16 h-16 rounded-2xl bg-neutral-100 flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">🔄</span>
          </div>
          <h2 className="text-lg font-semibold text-neutral-800 mb-2">
            Brak zanonimizowanych dokumentów
          </h2>
          <p className="text-neutral-500 text-sm max-w-sm mx-auto">
            Najpierw zanonimizuj dokument i wyeksportuj go.
            Mapowanie pseudonimów zapisze się automatycznie.
          </p>
        </Card>
      ) : !restoredText ? (
        <div className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1.5">
              Dokument źródłowy
            </label>
            <select
              value={selectedCase}
              onChange={(e) => handleCaseChange(e.target.value)}
              className="h-10 w-full px-3 rounded-lg border border-neutral-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-violet-200 focus:border-violet-400 transition-colors"
            >
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} — {new Date(c.created_at).toLocaleDateString("pl-PL")}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1.5">
              Odpowiedź z AI
            </label>
            <Textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Wklej tekst zawierający [PERSON_1], [LOCATION_2] itp."
              className="min-h-[220px] font-mono text-sm"
            />
          </div>

          <Button
            onClick={handleRestore}
            size="lg"
            className="w-full bg-gradient-to-r from-violet-500 to-indigo-600 hover:from-violet-600 hover:to-indigo-700 shadow-sm shadow-violet-200"
            disabled={!selectedCase || !inputText.trim() || loading}
          >
            {loading ? "Przywracam..." : "Przywróć oryginalne dane"}
          </Button>
        </div>
      ) : (
        <div>
          {/* Side by side view */}
          <div className="grid grid-cols-2 gap-6" style={{ height: "600px", overflow: "hidden" }}>
            <RestorePanel
              text={inputText}
              mapping={mapping}
              mode="pseudonymized"
              title="Odpowiedź z AI"
            />
            <RestorePanel
              text={restoredText}
              mapping={mapping}
              mode="restored"
              title="Z przywróconymi danymi"
            />
          </div>

          <div className="mt-6 text-center">
            <button
              onClick={() => {
                setRestoredText("");
                setInputText("");
              }}
              className="text-sm text-neutral-500 hover:text-neutral-700 transition-colors"
            >
              ← Przywróć kolejny tekst
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
