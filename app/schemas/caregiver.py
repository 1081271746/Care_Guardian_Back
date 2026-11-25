from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator

CaregiverRole = Literal["cuidador", "familiar", "profesional"]


class CaregiverAssignmentCreate(BaseModel):
    """Assign by user id (legacy) or by the caregiver's e-mail."""
    model_config = ConfigDict(extra="forbid")

    user_id: int | None = None
    email: EmailStr | None = None
    rol: CaregiverRole = "cuidador"

    @field_validator("email", mode="before")
    @classmethod
    def normalize(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @model_validator(mode="after")
    def one_identifier(self):
        if (self.user_id is None) == (self.email is None):
            raise ValueError("Indica user_id o email del cuidador")
        return self


class CaregiverResponse(BaseModel):
    user_id: int
    nombre: str
    email: str
    rol: str
