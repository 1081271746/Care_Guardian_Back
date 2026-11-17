from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

CONSENT_VERSION = "groq-minimized-v1"
DISCLAIMER = (
    "Interpretación descriptiva, no diagnóstico ni conclusión clínica. "
    "No modifica medicamentos ni tratamientos. Consulta con un profesional sanitario."
)


class Period(BaseModel):
    desde: date | None = None
    hasta: date | None = None

    @model_validator(mode="after")
    def valid_period(self):
        if self.desde and self.hasta and self.desde > self.hasta:
            raise ValueError("La fecha inicial debe ser anterior a la final")
        return self


class AnalysisRequest(Period):
    consentimiento: Literal[True]
    version_consentimiento: Literal["groq-minimized-v1"]


class AISelection(BaseModel):
    """Only references to verified facts can cross the model/output boundary."""
    model_config = ConfigDict(extra="forbid")
    resumen: list[str] = Field(min_length=1, max_length=6)
    revisar: list[str] = Field(max_length=4)
