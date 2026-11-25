"""Reusable Pydantic field types with consistent, Spanish validation rules."""
import re
from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, StringConstraints

from app.core.time import as_utc, utc_now


def _no_control_characters(value: str) -> str:
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise ValueError("El texto contiene caracteres no permitidos")
    return value


def Text(max_length: int, min_length: int = 1):
    """Trimmed text that cannot be blank or contain control characters."""
    return Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length),
        AfterValidator(_no_control_characters),
    ]


def OptionalText(max_length: int):
    """Optional text where an empty string means "not provided"."""
    def validate(value: str | None) -> str | None:
        if value is None:
            return None
        value = _no_control_characters(value.strip())
        if not value:
            return None
        if len(value) > max_length:
            raise ValueError(f"Máximo {max_length} caracteres")
        return value
    return Annotated[str | None, AfterValidator(validate)]


PHONE_PATTERN = re.compile(r"^\+?[0-9 ()\-]{7,20}$")


def _phone(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    value = value.strip()
    if not PHONE_PATTERN.match(value):
        raise ValueError("Teléfono no válido: usa entre 7 y 20 dígitos, espacios, guiones o +")
    return value


Phone = Annotated[str | None, AfterValidator(_phone)]

HOUR_PATTERN = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"


def not_in_future(value: datetime | None) -> datetime | None:
    """Observations can be registered late, never in the future."""
    if value is None:
        return None
    value = as_utc(value)
    if value > utc_now():
        raise ValueError("La fecha del registro no puede estar en el futuro")
    if value.year < 2000:
        raise ValueError("La fecha del registro no es válida")
    return value


PastTimestamp = Annotated[datetime | None, AfterValidator(not_in_future)]


def plausible_birth_date(value: date) -> date:
    today = date.today()
    if value > today:
        raise ValueError("La fecha de nacimiento no puede estar en el futuro")
    if value.year < 1900:
        raise ValueError("La fecha de nacimiento no es válida")
    return value


BirthDate = Annotated[date, AfterValidator(plausible_birth_date)]
