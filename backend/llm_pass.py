import json
import re
import requests
from pathlib import Path


def _load_default_prompt():
    path = Path(__file__).parent / "default_prompt.txt"
    return path.read_text(encoding="utf-8").strip()


DEFAULT_PROMPT = _load_default_prompt()


def get_prompt(settings: dict = None) -> str:
    """Get the LLM prompt — from settings if customized, otherwise default."""
    if settings and settings.get("llm_prompt"):
        return settings["llm_prompt"]
    return DEFAULT_PROMPT


JSON_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Exact quote from the document"},
            "reason": {"type": "string", "description": "Short explanation in Polish"},
        },
        "required": ["text", "reason"],
    },
}


def check_ollama_status(model="SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M"):
    """Check if Ollama is running and the model is available."""
    try:
        resp = requests.get("http://host.docker.internal:11434/api/tags", timeout=3)
        if resp.status_code != 200:
            return {"available": False, "ollama_running": False, "model_installed": False}
        models = [m["name"] for m in resp.json().get("models", [])]
        return {
            "available": model in models,
            "ollama_running": True,
            "model_installed": model in models,
            "models": models,
        }
    except requests.ConnectionError:
        # Try localhost (non-Docker)
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=3)
            if resp.status_code != 200:
                return {"available": False, "ollama_running": False, "model_installed": False}
            models = [m["name"] for m in resp.json().get("models", [])]
            return {
                "available": model in models,
                "ollama_running": True,
                "model_installed": model in models,
                "models": models,
            }
        except Exception:
            return {"available": False, "ollama_running": False, "model_installed": False}
    except Exception:
        return {"available": False, "ollama_running": False, "model_installed": False}


def _get_ollama_url():
    """Try Docker internal host first, then localhost."""
    for base in ["http://host.docker.internal:11434", "http://localhost:11434"]:
        try:
            requests.get(f"{base}/api/tags", timeout=2)
            return base
        except Exception:
            continue
    return "http://localhost:11434"


def find_contextual_identifiers(text, model="SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M", on_progress=None, settings=None):
    """Find contextual identifiers using local LLM.

    on_progress: optional callback(stage, tokens) called during generation.
    settings: dict with optional llm_prompt override.
    """
    base_url = _get_ollama_url()
    system_prompt = get_prompt(settings)

    if on_progress:
        on_progress("loading", 0)

    response = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "format": JSON_SCHEMA,
            "stream": True,
            "options": {"temperature": 0.1, "num_ctx": 32768},
        },
        timeout=180,
        stream=True,
    )
    response.raise_for_status()

    raw_parts = []
    token_count = 0
    for line in response.iter_lines():
        if not line:
            continue
        chunk = json.loads(line)
        msg = chunk.get("message", {})
        token = msg.get("content", "") or chunk.get("response", "")
        raw_parts.append(token)
        token_count += 1
        if on_progress and token_count % 5 == 0:
            on_progress("generating", token_count)
        if chunk.get("done"):
            break

    raw = "".join(raw_parts).strip()
    if on_progress:
        on_progress("parsing", token_count)

    # Strip <think>...</think> blocks from reasoning models (deepseek-r1, etc.)
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # Strip markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    # Extract JSON array — some models add text before/after
    bracket_start = raw.find("[")
    bracket_end = raw.rfind("]")
    if bracket_start >= 0 and bracket_end > bracket_start:
        raw = raw[bracket_start:bracket_end + 1]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []
