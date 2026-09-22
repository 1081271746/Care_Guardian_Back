from datetime import date, datetime

from pydantic import BaseModel


class PatientCreate(BaseModel):
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    documento: str
    telefono: str | None = None
    direccion: str | None = None
    contacto_emergencia: str | None = None
    telefono_emergencia: str | None = None


class PatientUpdate(BaseModel):
    nombres: str | None = None
    apellidos: str | None = None
    fecha_nacimiento: date | None = None
    documento: str | None = None
    telefono: str | None = None
    direccion: str | None = None
    contacto_emergencia: str | None = None
    telefono_emergencia: str | None = None
    activo: bool | None = None


class PatientResponse(BaseModel):
    id: int
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    documento: str
    telefono: str | None
    direccion: str | None
    contacto_emergencia: str | None
    telefono_emergencia: str | None
    activo: bool
    fecha_registro: datetime

    class Config:
        from_attributes = True