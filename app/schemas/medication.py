from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import HOUR_PATTERN, OptionalText, Text


class MedicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: Text(100)
    dosis: Text(100)
    frecuencia: Text(100)
    hora: str = Field(pattern=HOUR_PATTERN, description="Hora local en formato HH:MM")
    fecha_inicio: date
    fecha_fin: date | None = None
    indicaciones: OptionalText(300) = None

    @model_validator(mode="after")
    def valid_dates(self):
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de finalización no puede ser anterior a la de inicio")
        return self


class MedicationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: Text(100) | None = None
    dosis: Text(100) | None = None
    frecuencia: Text(100) | None = None
    hora: str | None = Field(default=None, pattern=HOUR_PATTERN)
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    indicaciones: OptionalText(300) = None
    activo: bool | None = None

    @model_validator(mode="after")
    def valid_dates(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de finalización no puede ser anterior a la de inicio")
        return self


class MedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
