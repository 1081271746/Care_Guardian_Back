from datetime import date, datetime

from pydantic import BaseModel


class MedicationCreate(BaseModel):
    nombre: str
    dosis: str
    frecuencia: str
    hora: str
    fecha_inicio: date
    fecha_fin: date | None = None
    indicaciones: str | None = None


class MedicationUpdate(BaseModel):
    nombre: str | None = None
    dosis: str | None = None
    frecuencia: str | None = None
    hora: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    indicaciones: str | None = None
    activo: bool | None = None


class MedicationResponse(BaseModel):
    id: int
    patient_id: int
    nombre: str
    dosis: str
    frecuencia: str
    hora: str
    fecha_inicio: date
    fecha_fin: date | None
    indicaciones: str | None
    activo: bool
    fecha_registro: datetime

    class Config:
        from_attributes = True