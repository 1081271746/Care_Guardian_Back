import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import hash_password, verify_password
from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import PasswordChange, UserCreate, UserResponse, UserUpdate


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def require_self(user_id: int, current_user: User) -> None:
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este usuario")


def registration_enabled() -> bool:
    return os.getenv("ALLOW_PUBLIC_REGISTRATION", "true").strip().lower() in {"1", "true", "yes", "si", "sí"}


def email_taken(db: Session, email: str, *, exclude_id: int | None = None) -> bool:
    query = db.query(User.id).filter(func.lower(User.email) == email.lower())
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)
    return query.first() is not None


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Registrar un cuidador")
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    if not registration_enabled():
        raise HTTPException(status_code=403, detail="El registro público está deshabilitado")

    if email_taken(db, user_data.email):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")

    new_user = User(
        nombre=user_data.nombre,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        # The role is never taken from the request body.
        rol="cuidador",
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


@router.get("/", response_model=list[UserResponse], summary="Cuenta propia (lista de uno)")
def get_users(current_user: User = Depends(get_current_user)):
    # Caregivers never list other accounts.
    return [current_user]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current_user: User = Depends(get_current_user)):
    require_self(user_id, current_user)
    return current_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_self(user_id, current_user)
    if user_data.rol is not None and user_data.rol != current_user.rol:
        raise HTTPException(status_code=403, detail="No puedes cambiar tu rol")

    if user_data.email is not None and email_taken(db, user_data.email, exclude_id=user_id):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")

    if user_data.nombre is not None:
        current_user.nombre = user_data.nombre

    if user_data.email is not None:
        current_user.email = user_data.email

    if user_data.activo is not None:
        current_user.activo = user_data.activo

    db.commit()
    db.refresh(current_user)

    return current_user


@router.put("/{user_id}/password", summary="Cambiar la contraseña propia")
def change_password(
    user_id: int,
    body: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_self(user_id, current_user)
    if not verify_password(body.password_actual, current_user.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")
    current_user.password_hash = hash_password(body.password_nueva)
    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_self(user_id, current_user)
    db.delete(current_user)
    db.commit()

    return {
        "mensaje": "Usuario eliminado correctamente"
    }
