from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.core.security import ALGORITHM, SECRET_KEY, credential_fingerprint
from app.database.connection import get_db
from app.models.user import User

from sqlalchemy.orm import Session


security = HTTPBearer(auto_error=False)

UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db)
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inicia sesión para continuar",
            headers=UNAUTHORIZED_HEADERS,
        )
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers=UNAUTHORIZED_HEADERS,
            )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tu sesión expiró; inicia sesión nuevamente",
            headers=UNAUTHORIZED_HEADERS,
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers=UNAUTHORIZED_HEADERS,
        )

    try:
        user = db.get(User, int(user_id))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido", headers=UNAUTHORIZED_HEADERS)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers=UNAUTHORIZED_HEADERS,
        )

    fingerprint = payload.get("pwd")
    if fingerprint is not None and fingerprint != credential_fingerprint(user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tu contraseña cambió; inicia sesión nuevamente",
            headers=UNAUTHORIZED_HEADERS,
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    return user
