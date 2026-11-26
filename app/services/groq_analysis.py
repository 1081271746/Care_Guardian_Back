import copy
import json
import logging
import os

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.evolution import DISCLAIMER, AISelection

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
logger = logging.getLogger("careguardian.groq")


def _retry_after(response) -> str:
    try:
        seconds = int(float(response.headers.get("retry-after", "60")))
    except ValueError:
        seconds = 60
    return str(max(1, min(seconds, 300)))


def provider_error(response):
    """Translate provider statuses without forwarding their bodies."""
    status = response.status_code
    logger.warning("Groq respondió HTTP %s", status)
    if status == 429:
        return HTTPException(429, "Groq alcanzó su límite de solicitudes; inténtalo en unos segundos",
                             headers={"Retry-After": _retry_after(response)})
    if status in (401, 403):
        return HTTPException(503, "La credencial de Groq configurada en el servidor no es válida")
    if status == 404:
        return HTTPException(503, "El modelo de Groq configurado no está disponible")
    if status == 400:
        return HTTPException(502, "Groq rechazó la solicitud de análisis")
    return HTTPException(502, "Groq no está disponible en este momento")

SYSTEM_PROMPT = (
    "Selecciona hechos relevantes para un resumen descriptivo de seguimiento. "
    "Devuelve exclusivamente JSON con resumen (1 a 6 IDs de hechos) y revisar "
    "(0 a 4 IDs de hechos para comentar con un profesional). "
    "Usa solo claves del objeto hechos; no escribas texto libre. No diagnostiques, "
    "no recomiendes tratamientos ni atribuyas causalidad o tendencias clínicas. "
    "Prioriza mediciones sobre conteos. No interpretes ausencia de registros como ausencia de síntomas."
)


class GroqHTTPClient(httpx.Client):
    """Dedicated client type so provider mocks never intercept the API test client."""


def generate_analysis(data):
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "")
    if not api_key or not model:
        raise HTTPException(503, "El análisis IA no está configurado")
    facts = data["hechos"]
    payload = {
        "model": model,
        "temperature": 0,
        "max_completion_tokens": 2048,
        "reasoning_effort": "low",
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
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
            strict = payload["response_format"].get("json_schema", {}).get("strict")
            if response.status_code == 400 and strict:
                # Groq documents strict mode for gpt-oss, but reports of intermittent
                # json_validate_failed exist. Retry once in best-effort mode; the
                # server-side validation below still rejects anything off-schema.
                logger.info("Groq rechazó el modo estricto; reintento único en modo flexible")
                flexible = copy.deepcopy(payload)
                flexible["response_format"]["json_schema"]["strict"] = False
                response = client.post(
                    GROQ_URL, headers={"Authorization": f"Bearer {api_key}"}, json=flexible,
                )
        if response.status_code >= 400:
            raise provider_error(response)
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
        logger.warning("Groq no respondió en el tiempo configurado")
        raise HTTPException(504, "Groq no respondió a tiempo; tus registros siguen disponibles") from None
    except httpx.HTTPError as error:
        logger.warning("No fue posible contactar a Groq: %s", type(error).__name__)
        raise HTTPException(502, "No fue posible contactar a Groq") from None
    except (ValidationError, ValueError, KeyError, IndexError, TypeError) as error:
        # Never expose provider bodies, keys or sensitive request data.
        logger.warning("Respuesta de Groq descartada por validación: %s", type(error).__name__)
        raise HTTPException(502, "No se pudo obtener una respuesta válida de Groq") from None
