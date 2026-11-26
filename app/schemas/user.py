from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.common import Text


def _normalize_email(value):
    return value.strip().lower() if isinstance(value, str) else value


class UserCreate(BaseModel):
    nombre: Text(100, min_length=2)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    _email = field_validator("email", mode="before")(_normalize_email)

    @field_validator("password")
    @classmethod
    def strong_enough(cls, value: str) -> str:
        if value.strip() != value:
            raise ValueError("La contraseña no puede empezar ni terminar con espacios")
        if value.isdigit() or value.isalpha():
            raise ValueError("La contraseña debe combinar letras y números")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    _email = field_validator("email", mode="before")(_normalize_email)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: Text(100, min_length=2) | None = None
    email: EmailStr | None = None
    rol: str | None = None
    activo: bool | None = None

    _email = field_validator("email", mode="before")(_normalize_email)


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password_actual: str = Field(min_length=1, max_length=128)
    password_nueva: str = Field(min_length=8, max_length=128)

    @field_validator("password_nueva")
    @classmethod
    def strong_enough(cls, value: str) -> str:
        return UserCreate.strong_enough(value)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: EmailStr
    rol: str
    activo: bool


class CurrentUserResponse(UserResponse):
    fecha_creacion: datetime
    pacientes_asignados: int
