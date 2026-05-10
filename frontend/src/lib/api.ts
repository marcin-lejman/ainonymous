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
