const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Entity {
  text: string;
  type: string;
  start: number;
  end: number;
  score: number;
  source: string;
  reason?: string;
}

export interface CaseSummary {
  id: string;
  name: string;
  created_at: string;
  entity_count: number;
  has_pseudonymized: boolean;
}

export interface CaseData {
  id: string;
  name: string;
  created_at: string;
  original_text: string;
  entities: Entity[];
  approved: Record<string, boolean>;
  pseudonymized_text: string | null;
  mapping: { forward: Record<string, string>; reverse: Record<string, string> } | null;
}

export interface OllamaStatus {
  available: boolean;
  ollama_running: boolean;
  model_installed: boolean;
  models?: string[];
  selected_model?: string | null;
}

export async function fetchCases(): Promise<CaseSummary[]> {
  const res = await fetch(`${API_BASE}/api/cases`);
  return res.json();
}

export async function fetchCase(id: string): Promise<CaseData> {
  const res = await fetch(`${API_BASE}/api/case/${id}`);
  return res.json();
}

export async function analyzeDocument(formData: FormData): Promise<{ case_id: string; entity_count: number }> {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function updateEntities(
  caseId: string,
  entities: Entity[],
  approved: Record<string, boolean>
): Promise<void> {
  await fetch(`${API_BASE}/api/case/${caseId}/entities`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entities, approved }),
  });
}

export async function pseudonymize(caseId: string): Promise<{
  pseudonymized_text: string;
  mapping_summary: { total: number; types: string[] };
}> {
  const res = await fetch(`${API_BASE}/api/case/${caseId}/pseudonymize`, {
    method: "POST",
  });
  return res.json();
}

export async function restoreText(caseId: string, text: string): Promise<{ restored_text: string }> {
  const res = await fetch(`${API_BASE}/api/case/${caseId}/restore`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ case_id: caseId, text }),
  });
  return res.json();
}

export async function deleteCase(caseId: string): Promise<void> {
  await fetch(`${API_BASE}/api/case/${caseId}`, { method: "DELETE" });
}

export async function checkOllama(): Promise<OllamaStatus> {
  try {
    const res = await fetch(`${API_BASE}/api/ollama/status`);
    return res.json();
  } catch {
    return { available: false, ollama_running: false, model_installed: false };
  }
}

export async function getSettings(): Promise<Record<string, string>> {
  const res = await fetch(`${API_BASE}/api/settings`);
  return res.json();
}

export async function updateSettings(settings: Record<string, string | null>): Promise<void> {
  await fetch(`${API_BASE}/api/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
}

export async function getDefaultPrompt(): Promise<string> {
  const res = await fetch(`${API_BASE}/api/settings/default-prompt`);
  const data = await res.json();
  return data.prompt;
}

export function streamLlmPass(
  caseId: string,
  onProgress: (data: { stage: string; tokens: number; found?: number; message?: string }) => void,
  onDone: () => void,
) {
  fetch(`${API_BASE}/api/case/${caseId}/llm-pass`, { method: "POST" }).then(async (response) => {
    const reader = response.body?.getReader();
    if (!reader) return;
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            onProgress(data);
            if (data.stage === "done" || data.stage === "error") {
              onDone();
              return;
            }
          } catch { /* ignore parse errors */ }
        }
      }
    }
    onDone();
  });
}

export async function addEntity(
  caseId: string,
  text: string,
  type: string
): Promise<void> {
  await fetch(`${API_BASE}/api/case/${caseId}/add-entity`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, type }),
  });
}
