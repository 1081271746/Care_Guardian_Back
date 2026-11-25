import os
from datetime import timedelta

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

from app.core.time import utc_now

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


def _expire_minutes() -> int:
    try:
        value = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    except ValueError:
        value = 60
    # Between 5 minutes and 24 hours; long-lived tokens are not revocable.
    return max(5, min(value, 1440))


ACCESS_TOKEN_EXPIRE_MINUTES = _expire_minutes()

password_hash = PasswordHash.recommended()
# Used to spend the same time verifying when the e-mail does not exist.
_DUMMY_HASH = password_hash.hash("careguardian-timing-equalizer")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(password, hashed_password)
    except Exception:
        # A corrupted or legacy hash must not become a 500 on login.
        return False


def spend_password_check(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


def create_access_token(data: dict) -> str:
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY no está configurada")
    now = utc_now()
    to_encode = data.copy()
    to_encode.update({
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
