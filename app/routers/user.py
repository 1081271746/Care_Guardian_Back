from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
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


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()

    return users

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    if user_data.nombre is not None:
        user.nombre = user_data.nombre

    if user_data.email is not None:
        user.email = user_data.email

    if user_data.rol is not None:
        user.rol = user_data.rol

    if user_data.activo is not None:
        user.activo = user_data.activo

    db.commit()
    db.refresh(user)

    return user