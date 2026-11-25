from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.common import Text

AlertLevel = Literal["bajo", "medio", "alto"]
AlertStatus = Literal["pendiente", "en_revision", "atendida", "descartada"]
CLOSED_STATUSES = {"atendida", "descartada"}


class AlertCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo: Text(50, min_length=3) = "manual"
    nivel: AlertLevel = "medio"
    titulo: Text(150, min_length=3)
    mensaje: Text(5000, min_length=5)
    estado: AlertStatus = "pendiente"
    # Manual alerts are always created by a person; system origins are reserved.
    origen: Literal["manual"] = "manual"


class AlertUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nivel: AlertLevel | None = None
    titulo: Text(150, min_length=3) | None = None
    mensaje: Text(5000, min_length=5) | None = None
    estado: AlertStatus | None = None
    activa: bool | None = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    symptom_id: int | None
    note_id: int | None
    tipo: str
    nivel: str
    titulo: str
    mensaje: str
    estado: str
    origen: str
    fecha_registro: datetime
    activa: bool
