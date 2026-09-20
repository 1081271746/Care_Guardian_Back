from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import UserCreate
from pwdlib import PasswordHash


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

password_hash = PasswordHash.recommended()


@router.post("/")
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    hashed_password = password_hash.hash(user_data.password)

    new_user = User(
        nombre=user_data.nombre,
        email=user_data.email,
        password_hash=hashed_password,
        rol=user_data.rol
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "mensaje": "Usuario creado correctamente",
        "usuario": {
            "id": new_user.id,
            "nombre": new_user.nombre,
            "email": new_user.email,
            "rol": new_user.rol
        }
    }

    