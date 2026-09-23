from datetime import datetime

from pydantic import BaseModel, Field


class SymptomRecordCreate(BaseModel):
    calidad_sueno: int | None = Field(
        default=None,
        ge=0,
        le=10
    )

    estado_animo: str | None = None

    apetito: str | None = None

    nivel_dolor: int | None = Field(
        default=None,
        ge=0,
        le=10
    )

    temperatura: float | None = Field(
        default=None,
        ge=30,
        le=45
    )

    observaciones: str | None = None

    nivel_gravedad: str = "bajo"


class SymptomRecordUpdate(BaseModel):
    calidad_sueno: int | None = Field(
        default=None,
        ge=0,
        le=10
    )

    estado_animo: str | None = None

    apetito: str | None = None

    nivel_dolor: int | None = Field(
        default=None,
        ge=0,
        le=10
    )

    temperatura: float | None = Field(
        default=None,
        ge=30,
        le=45
    )

    observaciones: str | None = None

    nivel_gravedad: str | None = None

    activo: bool | None = None


class SymptomRecordResponse(BaseModel):
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

    class Config:
        from_attributes = True