import json
import os
import httpx
from fastapi import HTTPException
from pydantic import ValidationError
from app.schemas.evolution import AISelection, DISCLAIMER

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

class GroqHTTPClient(httpx.Client):
    """Dedicated client type so provider mocks never intercept the API test client."""


def generate_analysis(data):
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "")
    if not api_key or not model:
        raise HTTPException(503, "El análisis IA no está configurado")
    facts = data["hechos"]
    payload = {
        "model": model, "temperature": 0, "max_completion_tokens": 2048,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content":
             "Selecciona hechos relevantes para un resumen descriptivo de seguimiento. "
             "Devuelve exclusivamente JSON con resumen (1 a 6 IDs de hechos) y revisar "
             "(0 a 4 IDs de hechos para comentar con un profesional). "
             "Usa solo claves del objeto hechos; no escribas texto libre. No diagnostiques, "
             "no recomiendes tratamientos ni atribuyas causalidad o tendencias clínicas. "
             "Prioriza mediciones sobre conteos. No interpretes ausencia de registros como ausencia de síntomas."},
            {"role": "user", "content": json.dumps({"hechos": facts}, ensure_ascii=False)},
        ],
    }
    if model in {"openai/gpt-oss-20b", "openai/gpt-oss-120b"}:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "evolution_fact_selection", "strict": True,
                "schema": {
                    "type": "object", "additionalProperties": False,
                    "required": ["resumen", "revisar"],
                    "properties": {
                        name: {"type": "array", "items": {"type": "string", "enum": list(facts)}}
                        for name in ("resumen", "revisar")
                    },
                },
            },
        }
    try:
        timeout = max(1, min(float(os.getenv("GROQ_TIMEOUT_SECONDS", "30")), 120))
        with GroqHTTPClient(timeout=timeout) as client:
            response = client.post(
                GROQ_URL, headers={"Authorization": f"Bearer {api_key}"}, json=payload,
            )
        if response.status_code == 429:
            raise HTTPException(503, "Groq está ocupado; inténtalo más tarde")
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if len(content) > 12000:
            raise ValueError("Output too large")
        selection = AISelection.model_validate_json(content)
        for reference in selection.resumen + selection.revisar:
            if reference not in facts:
                raise ValueError("Unknown fact")
        return {
            "resumen": [facts[k] for k in dict.fromkeys(selection.resumen)],
            "revisar": [facts[k] for k in dict.fromkeys(selection.revisar)],
            "advertencia": DISCLAIMER, "periodo": data["periodo"],
            "metodo": "Groq selecciona hechos; el servidor muestra únicamente textos verificados.",
        }
    except httpx.TimeoutException:
        raise HTTPException(504, "Groq no respondió a tiempo; tus registros siguen disponibles")
    except (httpx.HTTPError, ValidationError, ValueError, KeyError, IndexError, TypeError):
        # Never expose provider bodies, keys or sensitive request data.
        raise HTTPException(502, "No se pudo obtener una respuesta válida de Groq")
