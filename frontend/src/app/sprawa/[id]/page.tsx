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
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { getEntityColor } from "@/lib/entity-colors";

export default function SprawaPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [caseData, setCaseData] = useState<CaseData | null>(null);
  const [approved, setApproved] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [pseudoText, setPseudoText] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const originalPanelRef = useRef<HTMLDivElement>(null);

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

  function handleToggle(index: number, value: boolean) {
    const newApproved = { ...approved, [String(index)]: value };
    setApproved(newApproved);
    if (caseData) {
      updateEntities(id, caseData.entities, newApproved);
    }
  }

  async function handlePseudonymize() {
    setSaving(true);
    const result = await pseudonymize(id);
    setPseudoText(result.pseudonymized_text);
    // Reload case to get mapping
    const updated = await fetchCase(id);
    setCaseData(updated);
    setSaving(false);
  }

  async function handleAddFromSelection(text: string, type: string) {
    await addEntity(id, text, type);
    const updated = await fetchCase(id);
    setCaseData(updated);
    setApproved(updated.approved);
  }

  async function handleCopy() {
    if (pseudoText) {
      await navigator.clipboard.writeText(pseudoText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  function handleDownload() {
    if (!pseudoText || !caseData) return;
    const blob = new Blob([pseudoText], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${caseData.name.replace(/\s+/g, "_")}_anonimizacja.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading || !caseData) {
    return (
      <div className="text-neutral-400 text-sm py-12 text-center">
        Wczytywanie sprawy...
      </div>
    );
  }

  const activeCount = Object.values(approved).filter(Boolean).length;
  const totalCount = caseData.entities.length;
  const llmCount = caseData.entities.filter((e) => e.source === "llm").length;

  // Gather unique types for legend
  const uniqueTypes = [...new Set(caseData.entities.map((e) => e.type))];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/")}
              className="text-neutral-400 hover:text-neutral-600 transition-colors"
            >
              ← Dokumenty
            </button>
            <span className="text-neutral-300">/</span>
            <h1 className="text-xl font-semibold text-neutral-900">
              {caseData.name}
            </h1>
          </div>
          <p className="text-neutral-500 text-xs mt-1">
            {new Date(caseData.created_at).toLocaleDateString("pl-PL", {
              day: "numeric",
              month: "long",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        </div>
      </div>

      {/* Stats + Legend */}
      <div className="flex items-center gap-6 mb-6">
        <div className="flex items-center gap-4 text-sm">
          <span className="text-neutral-500">
            <span className="font-semibold text-neutral-800">{activeCount}</span>
            <span className="text-neutral-400">/{totalCount}</span> aktywnych
          </span>
          {llmCount > 0 && (
            <span className="text-neutral-500">
              🤖 {llmCount} z AI
            </span>
          )}
        </div>
        <Separator orientation="vertical" className="h-4" />
        <div className="flex items-center gap-2 flex-wrap">
          {uniqueTypes.map((type) => {
            const color = getEntityColor(type);
            return (
              <Badge
                key={type}
                variant="outline"
                className={`text-[10px] ${color.bg} ${color.fg} border`}
              >
                {color.label}
              </Badge>
            );
          })}
        </div>
      </div>

      <Tabs defaultValue="review" className="space-y-6">
        <TabsList>
          <TabsTrigger value="review">Przegląd</TabsTrigger>
          <TabsTrigger value="export">
            {pseudoText ? "Eksport" : "Zatwierdź"}
          </TabsTrigger>
        </TabsList>

        {/* Review Tab */}
        <TabsContent value="review" className="space-y-6">
          {/* Side by side documents */}
          <div className="grid grid-cols-2 gap-6 h-[500px]">
            <div className="relative min-h-0">
              <DocumentPanel
                ref={originalPanelRef}
                text={caseData.original_text}
                entities={caseData.entities}
                approved={approved}
                mode="original"
                title="Oryginał — podświetlone dane"
              />
              <SelectionPopup
                containerRef={originalPanelRef}
                onAdd={handleAddFromSelection}
              />
            </div>
            <DocumentPanel
              text={caseData.original_text}
              entities={caseData.entities}
              approved={approved}
              mode="pseudonymized"
              title="Podgląd anonimizacji"
            />
          </div>

          {/* Entity List */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-wide">
                Wykryte encje
              </h3>
              <p className="text-xs text-neutral-400">
                Wyłącz przełącznik, aby zachować oryginalne dane
              </p>
            </div>
            <Card className="p-2">
              <EntityList
                entities={caseData.entities}
                approved={approved}
                onToggle={handleToggle}
              />
            </Card>
          </div>

        </TabsContent>

        {/* Export Tab */}
        <TabsContent value="export" className="space-y-6">
          {!pseudoText ? (
            <Card className="p-8 text-center">
              <div className="w-12 h-12 rounded-xl bg-neutral-100 flex items-center justify-center mx-auto mb-4">
                <span className="text-lg">✅</span>
              </div>
              <h2 className="text-lg font-medium text-neutral-800 mb-2">
                Gotowe do anonimizacji
              </h2>
              <p className="text-sm text-neutral-500 mb-6 max-w-md mx-auto">
                {activeCount} encji zostanie zastąpionych pseudonimami.
                Sprawdź listę na zakładce &quot;Przegląd&quot; przed zatwierdzeniem.
              </p>
              <Button onClick={handlePseudonymize} size="lg" disabled={saving}>
                {saving ? "Przetwarzam..." : "Zatwierdź i zanonimizuj"}
              </Button>
            </Card>
          ) : (
            <div className="space-y-6">
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-neutral-700">
                    Zanonimizowany dokument
                  </h3>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={handleCopy}>
                      {copied ? "Skopiowano!" : "Kopiuj"}
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleDownload}>
                      Pobierz .txt
                    </Button>
                  </div>
                </div>
                <Textarea
                  value={pseudoText}
                  readOnly
                  className="min-h-[300px] font-mono text-sm bg-neutral-50"
                />
              </Card>

              <div className="bg-green-50 border border-green-100 rounded-xl p-4">
                <p className="text-sm text-green-800 font-medium mb-1">
                  Dokument jest bezpieczny do wysłania
                </p>
                <p className="text-xs text-green-700">
                  Wszystkie dane osobowe zostały zastąpione pseudonimami.
                  Skopiuj tekst i wklej go do Claude lub innego narzędzia AI.
                  Aby przywrócić oryginalne dane w odpowiedzi, użyj zakładki &quot;Przywróć dane&quot;.
                </p>
              </div>

              <Button
                variant="outline"
                onClick={handlePseudonymize}
                className="w-full"
              >
                Zanonimizuj ponownie (po zmianach)
              </Button>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
