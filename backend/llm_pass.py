import json
import re
import requests

SYSTEM_PROMPT = """Jesteś audytorem prywatności analizującym dokumenty prawne.
Twoim zadaniem jest znalezienie KONTEKSTOWYCH identyfikatorów osobowych — fraz,
które mogą jednoznacznie zidentyfikować osobę, nawet jeśli nie podano jej imienia
ani nazwiska.

Przykłady fraz do oznaczenia:
- Rola połączona z lokalizacją ("jedyna wspólniczka w warszawskim biurze")
- Relacje rodzinne z identyfikującym szczegółem ("syn Wynajmującej, który prowadzi praktykę adwokacką w tym samym budynku")
- Rola powiązana z czasem ("prezes, który odszedł w marcu 2023")
- Unikalne opisy ("wieloletni najemca sąsiedniego lokalu, emerytowany profesor")

NIE oznaczaj:
- Ogólnych ról bez identyfikujących szczegółów ("powód", "spółka", "Najemca")
- Już nazwanych osób z imienia i nazwiska (te są obsługiwane osobno przez inny system)
- Zwykłych stanowisk bez kontekstu
- Nazw firm i organizacji (te są obsługiwane osobno)

WAŻNE: W polu "text" podaj DOKŁADNY cytat z dokumentu — skopiuj tekst słowo w słowo,
zachowując oryginalną odmianę gramatyczną (przypadki, końcówki). NIE zmieniaj formy wyrazów.

Odpowiedz tablicą JSON obiektów, każdy z polami "text" (DOKŁADNY cytat z dokumentu)
i "reason" (jedno krótkie zdanie wyjaśniające dlaczego). Jeśli nic nie kwalifikuje się, zwróć [].
Odpowiedz WYŁĄCZNIE tablicą JSON, bez żadnego innego tekstu."""


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


def find_contextual_identifiers(text, model="SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M"):
    base_url = _get_ollama_url()
    response = requests.post(
        f"{base_url}/api/generate",
        json={
            "model": model,
            "prompt": f"{SYSTEM_PROMPT}\n\nDocument:\n{text}\n\nJSON output:",
            "stream": False,
            "options": {"temperature": 0.1},
        },
        timeout=120,
    )
    response.raise_for_status()
    raw = response.json()["response"].strip()

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
