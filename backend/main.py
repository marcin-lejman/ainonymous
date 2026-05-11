import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from analyzer import analyze_text
from llm_pass import check_ollama_status, find_contextual_identifiers

app = FastAPI(title="Anonymization Layer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("/data") if Path("/data").exists() else Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# --- Models ---

class AnalyzeRequest(BaseModel):
    text: str
    case_name: str
    use_llm: bool = False

class EntityUpdate(BaseModel):
    entities: list[dict]
    approved: dict[str, bool]

class RestoreRequest(BaseModel):
    case_id: str
    text: str


# --- Helpers ---

def extract_text_from_upload(file: UploadFile) -> str:
    name = file.filename.lower()
    content = file.file.read()
    if name.endswith(".txt"):
        return content.decode("utf-8")
    elif name.endswith(".docx"):
        import io
        from docx import Document
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    elif name.endswith(".pdf"):
        import io
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return "\n".join((page.extract_text() or "") for page in pdf.pages)
    return content.decode("utf-8", errors="replace")


def load_case(case_id: str) -> Optional[dict]:
    path = DATA_DIR / f"{case_id}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_case(case_data: dict):
    path = DATA_DIR / f"{case_data['id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(case_data, f, ensure_ascii=False, indent=2)


def build_pseudonymized(text: str, entities: list[dict], approved: dict[str, bool]) -> tuple[str, dict]:
    """Build pseudonymized text and return (text, forward_mapping)."""
    active = [
        (i, ent) for i, ent in enumerate(entities)
        if approved.get(str(i), True)
    ]
    active.sort(key=lambda x: x[1]["start"])

    forward = {}  # real -> placeholder
    reverse = {}  # placeholder -> real
    type_counts = {}

    result = []
    last = 0
    for i, ent in active:
        key = f"{ent['type']}::{ent['text']}"
        if key not in forward:
            t = ent["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
            placeholder = f"[{t}_{type_counts[t]}]"
            forward[key] = placeholder
            reverse[placeholder] = ent["text"]

        result.append(text[last:ent["start"]])
        result.append(forward[key])
        last = ent["end"]
    result.append(text[last:])

    return "".join(result), {"forward": forward, "reverse": reverse}


def restore_text(text: str, mapping: dict) -> str:
    """Replace placeholders with real values, longest first."""
    reverse = mapping.get("reverse", {})
    for placeholder in sorted(reverse.keys(), key=len, reverse=True):
        text = text.replace(placeholder, reverse[placeholder])
    return text


SETTINGS_PATH = DATA_DIR / "settings.json"

def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_settings(settings: dict):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


# --- Endpoints ---

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/ollama/status")
def ollama_status():
    settings = load_settings()
    selected_model = settings.get("llm_model")
    status = check_ollama_status(model=selected_model or "SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M")
    status["selected_model"] = selected_model
    return status


@app.get("/api/settings")
def get_settings():
    return load_settings()


@app.put("/api/settings")
def update_settings(body: dict):
    settings = load_settings()
    settings.update(body)
    save_settings(settings)
    return settings


@app.get("/api/cases")
def list_cases():
    cases = []
    for path in sorted(DATA_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cases.append({
                "id": data["id"],
                "name": data["name"],
                "created_at": data["created_at"],
                "entity_count": len(data.get("entities", [])),
                "has_pseudonymized": bool(data.get("pseudonymized_text")),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return cases


@app.get("/api/case/{case_id}")
def get_case(case_id: str):
    case = load_case(case_id)
    if not case:
        return {"error": "Sprawa nie znaleziona"}, 404
    return case


@app.post("/api/analyze")
async def analyze(
    text: Optional[str] = Form(None),
    case_name: str = Form("Nowa sprawa"),
    use_llm: bool = Form(False),
    file: Optional[UploadFile] = File(None),
):
    # Extract text from file or use pasted text
    if file and file.filename:
        doc_text = extract_text_from_upload(file)
    elif text:
        doc_text = text
    else:
        return {"error": "Podaj tekst lub plik do analizy"}

    # Run Presidio
    results = analyze_text(doc_text)

    entities = []
    for r in results:
        entities.append({
            "text": doc_text[r.start:r.end],
            "type": r.entity_type,
            "start": r.start,
            "end": r.end,
            "score": round(r.score, 2),
            "source": "presidio",
        })

    # Run LLM pass if requested
    if use_llm:
        try:
            settings = load_settings()
            selected_model = settings.get("llm_model", "SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M")
            contextual = find_contextual_identifiers(doc_text, model=selected_model)
            for c in contextual:
                phrase = c["text"]
                idx = doc_text.find(phrase)

                # Fuzzy fallback
                if idx < 0:
                    words = phrase.split()
                    best_idx, best_len = -1, 0
                    for start_w in range(len(words)):
                        for end_w in range(len(words), start_w, -1):
                            sub = " ".join(words[start_w:end_w])
                            if len(sub) < 20:
                                continue
                            pos = doc_text.find(sub)
                            if pos >= 0 and len(sub) > best_len:
                                best_idx, best_len = pos, len(sub)
                                break
                    if best_idx >= 0:
                        phrase = doc_text[best_idx:best_idx + best_len]
                        idx = best_idx

                if idx >= 0:
                    entities.append({
                        "text": phrase,
                        "type": "CONTEXTUAL",
                        "start": idx,
                        "end": idx + len(phrase),
                        "score": 0.5,
                        "source": "llm",
                        "reason": c.get("reason", ""),
                    })
        except Exception as e:
            print(f"[LLM] Error: {e}")

    # Dedup: LLM subsumes Presidio
    llm_spans = [(e["start"], e["end"]) for e in entities if e["source"] == "llm"]
    filtered = [
        e for e in entities
        if not (e["source"] == "presidio" and any(
            ls <= e["start"] and e["end"] <= le for ls, le in llm_spans
        ))
    ]
    filtered.sort(key=lambda e: (-e["score"], e["start"]))
    seen_spans = []
    deduped = []
    for e in filtered:
        overlaps = any(not (e["end"] <= s[0] or e["start"] >= s[1]) for s in seen_spans)
        if not overlaps:
            deduped.append(e)
            seen_spans.append((e["start"], e["end"]))

    entities = sorted(deduped, key=lambda e: e["start"])

    # Create case
    case_id = str(uuid.uuid4())[:8]
    case_data = {
        "id": case_id,
        "name": case_name,
        "created_at": datetime.now().isoformat(),
        "original_text": doc_text,
        "entities": entities,
        "approved": {str(i): True for i in range(len(entities))},
        "pseudonymized_text": None,
        "mapping": None,
    }
    save_case(case_data)

    return {"case_id": case_id, "entity_count": len(entities)}


@app.put("/api/case/{case_id}/entities")
def update_entities(case_id: str, update: EntityUpdate):
    case = load_case(case_id)
    if not case:
        return {"error": "Sprawa nie znaleziona"}

    case["entities"] = update.entities
    case["approved"] = update.approved
    save_case(case)
    return {"ok": True}


@app.post("/api/case/{case_id}/pseudonymize")
def pseudonymize(case_id: str):
    case = load_case(case_id)
    if not case:
        return {"error": "Sprawa nie znaleziona"}

    pseudo_text, mapping = build_pseudonymized(
        case["original_text"],
        case["entities"],
        case["approved"],
    )
    case["pseudonymized_text"] = pseudo_text
    case["mapping"] = mapping
    save_case(case)

    return {
        "pseudonymized_text": pseudo_text,
        "mapping_summary": {
            "total": len(mapping["forward"]),
            "types": list(set(k.split("::")[0] for k in mapping["forward"])),
        },
    }


@app.post("/api/case/{case_id}/restore")
def restore(case_id: str, req: RestoreRequest):
    case = load_case(case_id)
    if not case:
        return {"error": "Sprawa nie znaleziona"}
    if not case.get("mapping"):
        return {"error": "Brak mapowania — najpierw zanonimizuj dokument"}

    restored = restore_text(req.text, case["mapping"])
    return {"restored_text": restored}


@app.delete("/api/case/{case_id}")
def delete_case(case_id: str):
    path = DATA_DIR / f"{case_id}.json"
    if path.exists():
        path.unlink()
    return {"ok": True}


@app.post("/api/case/{case_id}/add-entity")
def add_entity(case_id: str, entity: dict):
    case = load_case(case_id)
    if not case:
        return {"error": "Sprawa nie znaleziona"}

    text = entity.get("text", "")
    idx = case["original_text"].find(text)
    if idx < 0:
        return {"error": "Tekst nie znaleziony w dokumencie"}

    new_entity = {
        "text": text,
        "type": entity.get("type", "OTHER"),
        "start": idx,
        "end": idx + len(text),
        "score": 1.0,
        "source": "manual",
    }
    case["entities"].append(new_entity)
    case["entities"].sort(key=lambda e: e["start"])
    new_idx = str(len(case["entities"]) - 1)
    case["approved"][new_idx] = True
    # Reindex approved
    case["approved"] = {str(i): True for i in range(len(case["entities"]))}
    save_case(case)

    return {"ok": True, "entity_count": len(case["entities"])}
