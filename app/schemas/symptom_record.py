from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import OptionalText, PastTimestamp

Severity = Literal["bajo", "moderado", "grave"]


class SymptomRecordCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calidad_sueno: int | None = Field(default=None, ge=0, le=10)
    estado_animo: OptionalText(50) = None
    apetito: OptionalText(50) = None
    nivel_dolor: int | None = Field(default=None, ge=0, le=10)
    temperatura: float | None = Field(default=None, ge=30, le=45)
    observaciones: OptionalText(5000) = None
    nivel_gravedad: Severity = "bajo"
    fecha_registro: PastTimestamp = Field(
        default=None,
        description="Momento de la observación; por defecto, ahora. No puede ser futuro.",
    )


class SymptomRecordUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calidad_sueno: int | None = Field(default=None, ge=0, le=10)
    estado_animo: OptionalText(50) = None
    apetito: OptionalText(50) = None
    nivel_dolor: int | None = Field(default=None, ge=0, le=10)
    temperatura: float | None = Field(default=None, ge=30, le=45)
    observaciones: OptionalText(5000) = None
    nivel_gravedad: Severity | None = None
    activo: bool | None = None


class SymptomRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    caregiver_id: int
    calidad_sueno: int | None
    estado_animo: str | None
    apetito: str | None
    nivel_dolor: int | None
    temperatura: float | None
    observaciones: str | None
    nivel_gravedad: str
    fecha_registro: datetime
    activo: bool
    registrado_por_nombre: str | None = None
