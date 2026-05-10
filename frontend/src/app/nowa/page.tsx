"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { analyzeDocument, checkOllama, OllamaStatus } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

export default function NowaSprawaPage() {
  const [caseName, setCaseName] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [useLlm, setUseLlm] = useState(false);
  const [ollama, setOllama] = useState<OllamaStatus | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const router = useRouter();

  useEffect(() => {
    checkOllama().then(setOllama);
  }, []);

  async function handleAnalyze() {
    if (!text.trim() && !file) return;

    setAnalyzing(true);
    setProgress(20);

    const formData = new FormData();
    formData.append("case_name", caseName || "Nowa sprawa");
    formData.append("use_llm", String(useLlm));

    if (file) {
      formData.append("file", file);
    } else {
      formData.append("text", text);
    }

    setProgress(50);

    try {
      const result = await analyzeDocument(formData);
      setProgress(100);
      setTimeout(() => {
        router.push(`/sprawa/${result.case_id}`);
      }, 300);
    } catch (e) {
      setAnalyzing(false);
      setProgress(0);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-neutral-900">Nowa sprawa</h1>
        <p className="text-neutral-500 text-sm mt-1">
          Prześlij dokument lub wklej tekst do anonimizacji
        </p>
      </div>

      {analyzing ? (
        <Card className="p-8">
          <div className="text-center">
            <div className="w-12 h-12 rounded-xl bg-neutral-100 flex items-center justify-center mx-auto mb-4 animate-pulse">
              <span className="text-lg">🔍</span>
            </div>
            <h2 className="text-lg font-medium text-neutral-800 mb-2">
              Analizuję dokument...
            </h2>
            <p className="text-sm text-neutral-500 mb-6">
              {useLlm
                ? "Presidio + Bielik szukają danych osobowych. To może potrwać do 30 sekund."
                : "Presidio szuka danych osobowych w tekście."}
            </p>
            <Progress value={progress} className="max-w-xs mx-auto" />
          </div>
        </Card>
      ) : (
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1.5">
              Nazwa sprawy
            </label>
            <Input
              value={caseName}
              onChange={(e) => setCaseName(e.target.value)}
              placeholder="np. Umowa najmu Kowalski"
              className="max-w-md"
            />
            <p className="text-xs text-neutral-400 mt-1">
              Pomaga odnaleźć sprawę później. Możesz zostawić puste.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1.5">
              Dokument
            </label>
            <div className="border-2 border-dashed border-neutral-200 rounded-xl p-6 text-center hover:border-neutral-300 transition-colors">
              <input
                type="file"
                accept=".txt,.docx,.pdf"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center mx-auto mb-3">
                  <span className="text-sm">📎</span>
                </div>
                {file ? (
                  <p className="text-sm font-medium text-neutral-800">{file.name}</p>
                ) : (
                  <>
                    <p className="text-sm text-neutral-600 font-medium">
                      Kliknij, aby wybrać plik
                    </p>
                    <p className="text-xs text-neutral-400 mt-1">
                      .txt, .docx lub .pdf
                    </p>
                  </>
                )}
              </label>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex-1 border-t border-neutral-100" />
            <span className="text-xs text-neutral-400">lub wklej tekst</span>
            <div className="flex-1 border-t border-neutral-100" />
          </div>

          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Wklej treść dokumentu tutaj..."
            className="min-h-[200px] font-mono text-sm"
            disabled={!!file}
          />

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-neutral-800">
                  Analiza kontekstowa (Bielik AI)
                </p>
                <p className="text-xs text-neutral-500 mt-0.5">
                  Wykrywa identyfikatory opisowe, np. &quot;jedyna wspólniczka w biurze&quot;
                </p>
              </div>
              <Switch
                checked={useLlm}
                onCheckedChange={setUseLlm}
                disabled={!ollama?.available}
              />
            </div>
            {ollama && !ollama.available && (
              <div className="mt-3 p-3 bg-amber-50 border border-amber-100 rounded-lg">
                <p className="text-xs font-medium text-amber-800 mb-1">
                  {!ollama.ollama_running
                    ? "Ollama nie jest uruchomiona"
                    : "Model Bielik nie jest zainstalowany"}
                </p>
                <p className="text-xs text-amber-700">
                  {!ollama.ollama_running ? (
                    <>
                      Zainstaluj Ollama ze strony{" "}
                      <span className="font-mono">ollama.com</span>, a następnie uruchom:{" "}
                      <code className="bg-amber-100 px-1 rounded">ollama serve</code>
                    </>
                  ) : (
                    <>
                      Pobierz model poleceniem:{" "}
                      <code className="bg-amber-100 px-1 rounded">
                        ollama pull SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M
                      </code>
                    </>
                  )}
                </p>
              </div>
            )}
          </Card>

          <Button
            onClick={handleAnalyze}
            size="lg"
            className="w-full"
            disabled={!text.trim() && !file}
          >
            Analizuj dokument
          </Button>
        </div>
      )}
    </div>
  );
}
