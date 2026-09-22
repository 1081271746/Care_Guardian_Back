from pydantic import BaseModel


class CaregiverAssignmentCreate(BaseModel):
    user_id: int
    rol: str = "cuidador"


class CaregiverResponse(BaseModel):
    user_id: int
    nombre: str
    email: str
    rol: str