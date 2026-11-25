from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import throttle
from app.core.dependencies import get_current_user
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    credential_fingerprint,
    spend_password_check,
    verify_password,
)
from app.database.connection import get_db
from app.models.patient_caregiver import PatientCaregiver
from app.models.user import User
from app.schemas.user import CurrentUserResponse, UserLogin


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales incorrectas",
)


@router.post("/login", summary="Iniciar sesión y obtener un token JWT")
def login(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    client = request.client.host if request.client else "desconocido"
    keys = (f"email:{user_data.email}", f"ip:{client}")
    wait = throttle.retry_after(*keys)
    if wait:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos; espera unos minutos e inténtalo de nuevo",
            headers={"Retry-After": str(wait)},
        )

    # E-mails are compared case-insensitively; legacy rows may contain capitals.
    user = db.query(User).filter(
        func.lower(User.email) == user_data.email
    ).first()

    if user is None:
        # Same password-hashing cost as a real account: no user enumeration by timing.
        spend_password_check(user_data.password)
        throttle.record_failure(*keys)
        raise INVALID_CREDENTIALS

    if not verify_password(user_data.password, user.password_hash):
        throttle.record_failure(*keys)
        raise INVALID_CREDENTIALS

    throttle.reset(keys[0])

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    access_token = create_access_token({
        "sub": str(user.id),
        "rol": user.rol,
        "pwd": credential_fingerprint(user.password_hash),
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.get("/me", response_model=CurrentUserResponse, summary="Usuario autenticado")
def me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assigned = db.query(func.count(PatientCaregiver.id)).filter(
        PatientCaregiver.user_id == current_user.id
    ).scalar()
    return CurrentUserResponse(
        id=current_user.id,
        nombre=current_user.nombre,
        email=current_user.email,
        rol=current_user.rol,
        activo=current_user.activo,
        fecha_creacion=current_user.fecha_creacion,
        pacientes_asignados=assigned or 0,
    )
