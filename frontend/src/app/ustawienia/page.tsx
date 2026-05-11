"use client";

import { useState, useEffect } from "react";
import { getSettings, updateSettings, getDefaultPrompt, checkOllama, OllamaStatus } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";

export default function UstawieniaPage() {
  const [prompt, setPrompt] = useState("");
  const [defaultPrompt, setDefaultPrompt] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [ollama, setOllama] = useState<OllamaStatus | null>(null);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getSettings(),
      getDefaultPrompt(),
      checkOllama(),
    ]).then(([settings, defPrompt, ollamaStatus]) => {
      setPrompt(settings.llm_prompt || defPrompt);
      setDefaultPrompt(defPrompt);
      setSelectedModel(settings.llm_model || "");
      setOllama(ollamaStatus);
      setLoading(false);
    });
  }, []);

  async function handleSavePrompt() {
    await updateSettings({ llm_prompt: prompt });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  async function handleResetPrompt() {
    setPrompt(defaultPrompt);
    await updateSettings({ llm_prompt: null as unknown as string });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  async function handleSaveModel(model: string) {
    setSelectedModel(model);
    await updateSettings({ llm_model: model });
  }

  if (loading) {
    return <div className="text-neutral-400 text-sm py-12 text-center">Wczytywanie...</div>;
  }

  const isModified = prompt !== defaultPrompt;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-neutral-900">Ustawienia</h1>
        <p className="text-neutral-500 text-sm mt-1">
          Konfiguracja modelu AI i promptu do analizy kontekstowej
        </p>
      </div>

      <div className="space-y-8">
        {/* Model selection */}
        <Card className="p-5">
          <h2 className="text-sm font-semibold text-neutral-800 mb-3">Model AI</h2>

          {ollama?.ollama_running && ollama.models && ollama.models.length > 0 ? (
            <>
              <select
                value={selectedModel}
                onChange={(e) => handleSaveModel(e.target.value)}
                className="h-10 w-full px-3 rounded-lg border border-neutral-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-violet-200 focus:border-violet-400 transition-colors"
              >
                {ollama.models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-neutral-400 mt-2">
                Zainstaluj nowe modele: <code className="bg-neutral-100 px-1 rounded">ollama pull nazwa_modelu</code>
              </p>
            </>
          ) : (
            <div className="p-3 bg-amber-50 border border-amber-100 rounded-lg">
              <p className="text-xs text-amber-800">
                {!ollama?.ollama_running
                  ? "Ollama nie jest uruchomiona. Uruchom: ollama serve"
                  : "Brak zainstalowanych modeli. Zainstaluj: ollama pull gemma4"}
              </p>
            </div>
          )}
        </Card>

        {/* Prompt editor */}
        <Card className="p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-sm font-semibold text-neutral-800">Prompt analizy kontekstowej</h2>
              <p className="text-xs text-neutral-500 mt-0.5">
                Instrukcja wysyłana do modelu AI. Dokument zostanie umieszczony w tagach &lt;document&gt;.
              </p>
            </div>
            {isModified && (
              <span className="text-[11px] text-amber-600 font-medium">Zmodyfikowany</span>
            )}
          </div>

          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="min-h-[400px] font-mono text-xs leading-5"
          />

          <div className="flex items-center justify-between mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={handleResetPrompt}
              disabled={!isModified}
            >
              Przywróć domyślny
            </Button>
            <Button
              onClick={handleSavePrompt}
              size="sm"
              className="bg-gradient-to-r from-violet-500 to-indigo-600 hover:from-violet-600 hover:to-indigo-700"
            >
              {saved ? "✓ Zapisano" : "Zapisz prompt"}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
