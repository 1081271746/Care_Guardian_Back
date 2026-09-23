from datetime import date, datetime, time

from pydantic import BaseModel


class AppointmentCreate(BaseModel):
    titulo: str
    especialidad: str
    profesional: str
    fecha: date
    hora: time
    lugar: str | None = None
    estado: str = "pendiente"
    notas: str | None = None


class AppointmentUpdate(BaseModel):
    titulo: str | None = None
    especialidad: str | None = None
    profesional: str | None = None
    fecha: date | None = None
    hora: time | None = None
    lugar: str | None = None
    estado: str | None = None
    notas: str | None = None


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    titulo: str
    especialidad: str
    profesional: str
    fecha: date
    hora: time
    lugar: str | None
    estado: str
    notas: str | None
    fecha_registro: datetime

    class Config:
        from_attributes = True