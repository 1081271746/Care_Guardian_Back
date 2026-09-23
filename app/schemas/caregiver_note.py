from datetime import datetime

from pydantic import BaseModel, Field


class CaregiverNoteCreate(BaseModel):
    contenido: str = Field(
        min_length=5,
        max_length=5000
    )


class CaregiverNoteUpdate(BaseModel):
    contenido: str | None = Field(
        default=None,
        min_length=5,
        max_length=5000
    )

    activo: bool | None = None


class CaregiverNoteResponse(BaseModel):
    id: int
    patient_id: int
    caregiver_id: int
    contenido: str
    fecha_registro: datetime
    activo: bool

    class Config:
        from_attributes = True