"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  fetchCase,
  updateEntities,
  pseudonymize,
  addEntity,
  CaseData,
} from "@/lib/api";
import { DocumentPanel } from "@/components/DocumentPanel";
import { EntityList } from "@/components/EntityList";
import { SelectionPopup } from "@/components/SelectionPopup";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

/**
 * Polish plural + adjective agreement for "encja aktywna".
 * 1 → "1 encja aktywna"
 * 2–4 (except 12–14) → "N encje aktywne"
 * 5+ and 12–14 → "N encji aktywnych"
 */
function encjeAktywne(n: number): string {
  if (n === 1) return "1 encja aktywna";
  const lastTwo = n % 100;
  const lastOne = n % 10;
  if (lastOne >= 2 && lastOne <= 4 && (lastTwo < 12 || lastTwo > 14)) {
    return `${n} encje aktywne`;
  }
  return `${n} encji aktywnych`;
}

function encjeTotal(n: number): string {
  if (n === 1) return "1 encja";
  const lastTwo = n % 100;
  const lastOne = n % 10;
  if (lastOne >= 2 && lastOne <= 4 && (lastTwo < 12 || lastTwo > 14)) {
    return `${n} encje`;
  }
  return `${n} encji`;
}

export default function SprawaPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [caseData, setCaseData] = useState<CaseData | null>(null);
  const [approved, setApproved] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [pseudoText, setPseudoText] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const originalPanelRef = useRef<HTMLDivElement>(null);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchCase(id).then((data) => {
      setCaseData(data);
      setApproved(data.approved);
      if (data.pseudonymized_text) {
        setPseudoText(data.pseudonymized_text);
      }
      setLoading(false);
    });
  }, [id]);

  // Close export menu on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (exportMenuRef.current && !exportMenuRef.current.contains(e.target as Node)) {
        setShowExportMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleToggle(index: number, value: boolean) {
    const newApproved = { ...approved, [String(index)]: value };
    setApproved(newApproved);
    setPseudoText(null); // invalidate previous export
    if (caseData) {
      updateEntities(id, caseData.entities, newApproved);
    }
  }

  async function handleExport(format: "clipboard" | "txt") {
    setSaving(true);
    const result = await pseudonymize(id);
    setPseudoText(result.pseudonymized_text);
    const updated = await fetchCase(id);
    setCaseData(updated);
    setSaving(false);
    setShowExportMenu(false);

    if (format === "clipboard") {
      await navigator.clipboard.writeText(result.pseudonymized_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } else {
      const blob = new Blob([result.pseudonymized_text], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${updated.name.replace(/\s+/g, "_")}_anonimizacja.txt`;
      a.click();
      URL.revokeObjectURL(url);
    }
  }

  async function handleAddFromSelection(text: string, type: string) {
    await addEntity(id, text, type);
    const updated = await fetchCase(id);
    setCaseData(updated);
    setApproved(updated.approved);
    setPseudoText(null);
  }

  if (loading || !caseData) {
    return (
      <div className="text-neutral-400 text-sm py-12 text-center">
        Wczytywanie dokumentu...
      </div>
    );
  }

  const activeCount = Object.values(approved).filter(Boolean).length;
  const totalCount = caseData.entities.length;
  const llmCount = caseData.entities.filter((e) => e.source === "llm").length;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/")}
            className="text-neutral-400 hover:text-neutral-600 transition-colors text-sm"
          >
            ← Dokumenty
          </button>
          <span className="text-neutral-200">/</span>
          <h1 className="text-lg font-semibold text-neutral-900">
            {caseData.name}
          </h1>
          <span className="text-sm text-neutral-500">
            · {activeCount}/{totalCount} {encjeAktywne(activeCount).split(" ").slice(1).join(" ")}
            {llmCount > 0 && <> · 🤖 {llmCount} z AI</>}
          </span>
        </div>

        {/* Export button */}
        <div className="relative" ref={exportMenuRef}>
          <Button
            onClick={() => setShowExportMenu((v) => !v)}
            disabled={saving}
            className="bg-gradient-to-r from-violet-500 to-indigo-600 hover:from-violet-600 hover:to-indigo-700 shadow-sm shadow-violet-200"
          >
            {saving ? "Przetwarzam..." : copied ? "✓ Skopiowano!" : "Eksportuj ▾"}
          </Button>
          {showExportMenu && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-lg shadow-neutral-200/50 border border-neutral-200 p-1.5 z-50">
              <button
                onClick={() => handleExport("clipboard")}
                className="flex items-center gap-3 w-full px-3 py-2.5 text-sm text-left rounded-lg hover:bg-neutral-50 transition-colors"
              >
                <span className="text-base">📋</span>
                <div>
                  <p className="font-medium text-neutral-800">Kopiuj do schowka</p>
                  <p className="text-[11px] text-neutral-400">Wklej bezpośrednio do Claude</p>
                </div>
              </button>
              <button
                onClick={() => handleExport("txt")}
                className="flex items-center gap-3 w-full px-3 py-2.5 text-sm text-left rounded-lg hover:bg-neutral-50 transition-colors"
              >
                <span className="text-base">📄</span>
                <div>
                  <p className="font-medium text-neutral-800">Pobierz jako .txt</p>
                  <p className="text-[11px] text-neutral-400">Zapisz zanonimizowany plik</p>
                </div>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Success banner after export */}
      {pseudoText && !saving && (
        <div className="bg-green-50 border border-green-100 rounded-xl px-4 py-3 mb-6 flex items-center gap-2 text-sm text-green-800">
          <span className="text-green-600">✓</span>
          Zanonimizowany tekst gotowy — wklej do Claude, a potem użyj &quot;Przywróć dane&quot;
        </div>
      )}

      {/* Side by side documents */}
      <div className="grid grid-cols-2 gap-6" style={{ height: "500px", overflow: "hidden" }}>
        <div className="relative flex flex-col min-h-0 h-full">
          <DocumentPanel
            ref={originalPanelRef}
            text={caseData.original_text}
            entities={caseData.entities}
            approved={approved}
            mode="original"
            title="Oryginał"
          />
          <SelectionPopup
            containerRef={originalPanelRef}
            onAdd={handleAddFromSelection}
          />
        </div>
        <div className="flex flex-col min-h-0 h-full">
          <DocumentPanel
            text={caseData.original_text}
            entities={caseData.entities}
            approved={approved}
            mode="pseudonymized"
            title="Zanonimizowany"
          />
        </div>
      </div>

      {/* Entity List */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-wide">
            Wykryte encje · {encjeTotal(totalCount)}
          </h3>
          <p className="text-xs text-neutral-400">
            Wyłącz przełącznik, aby zachować oryginalne dane
          </p>
        </div>
        <Card className="p-2 max-h-[400px] overflow-y-auto">
          <EntityList
            entities={caseData.entities}
            approved={approved}
            onToggle={handleToggle}
          />
        </Card>
      </div>
    </div>
  );
}
