from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: str = "cuidador"

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    nombre: str | None = None
    email: EmailStr | None = None
    rol: str | None = None
    activo: bool | None = None


class UserResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: str
    activo: bool

    class Config:
        from_attributes = True