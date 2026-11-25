from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, StringConstraints
from typing import Annotated

from app.schemas.common import BirthDate, OptionalText, Phone, Text

Document = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=30,
                      pattern=r"^[A-Za-z0-9.\-]+$"),
]


class PatientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombres: Text(100)
    apellidos: Text(100)
    fecha_nacimiento: BirthDate
    documento: Document
    telefono: Phone = None
    direccion: OptionalText(200) = None
    contacto_emergencia: OptionalText(150) = None
    telefono_emergencia: Phone = None


class PatientUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombres: Text(100) | None = None
    apellidos: Text(100) | None = None
    fecha_nacimiento: BirthDate | None = None
    documento: Document | None = None
    telefono: Phone = None
    direccion: OptionalText(200) = None
    contacto_emergencia: OptionalText(150) = None
    telefono_emergencia: Phone = None
    activo: bool | None = None


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
