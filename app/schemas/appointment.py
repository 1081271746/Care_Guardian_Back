from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.common import OptionalText, Text

AppointmentStatus = Literal["pendiente", "confirmada", "completada", "cancelada"]


class AppointmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: Text(150)
    especialidad: Text(100)
    profesional: Text(150)
    fecha: date
    hora: time
    lugar: OptionalText(200) = None
    estado: AppointmentStatus = "pendiente"
    notas: OptionalText(500) = None


class AppointmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: Text(150) | None = None
    especialidad: Text(100) | None = None
    profesional: Text(150) | None = None
    fecha: date | None = None
    hora: time | None = None
    lugar: OptionalText(200) = None
    estado: AppointmentStatus | None = None
    notas: OptionalText(500) = None


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
