from datetime import datetime

from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    tipo: str = Field(
        min_length=3,
        max_length=50
    )

    nivel: str = Field(
        default="medio",
        min_length=3,
        max_length=20
    )

    titulo: str = Field(
        min_length=3,
        max_length=150
    )

    mensaje: str = Field(
        min_length=5,
        max_length=5000
    )

    estado: str = Field(
        default="pendiente",
        min_length=3,
        max_length=20
    )

    origen: str = Field(
        default="sistema",
        min_length=3,
        max_length=30
    )


class AlertUpdate(BaseModel):
    nivel: str | None = Field(
        default=None,
        min_length=3,
        max_length=20
    )

    titulo: str | None = Field(
        default=None,
        min_length=3,
        max_length=150
    )

    mensaje: str | None = Field(
        default=None,
        min_length=5,
        max_length=5000
    )

    estado: str | None = Field(
        default=None,
        min_length=3,
        max_length=20
    )

    activa: bool | None = None


class AlertResponse(BaseModel):
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

    class Config:
        from_attributes = True