from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PastTimestamp, Text


class CaregiverNoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contenido: Text(5000, min_length=5)
    fecha_registro: PastTimestamp = Field(
        default=None,
        description="Momento de la observación; por defecto, ahora. No puede ser futuro.",
    )


class CaregiverNoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contenido: Text(5000, min_length=5) | None = None
    activo: bool | None = None


class CaregiverNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    caregiver_id: int
    contenido: str
    fecha_registro: datetime
    activo: bool
