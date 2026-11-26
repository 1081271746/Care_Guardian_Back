import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.environ["DATABASE_URL"].strip()
elif all((DB_HOST, DB_NAME, DB_USER)):
    DATABASE_URL = (
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD or ''}"
        f"@{DB_HOST}:{DB_PORT or 5432}/{DB_NAME}"
    )
else:
    # Fail at import with a clear message instead of connecting to "None:None@None".
    raise RuntimeError(
        "Configura DATABASE_URL (o DB_HOST, DB_NAME, DB_USER y DB_PASSWORD) antes de iniciar la API"
    )

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )

def _int_env(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, default)))
    except ValueError:
        return default


_pool_options = {} if DATABASE_URL.startswith("sqlite") else {
    "pool_size": _int_env("DB_POOL_SIZE", 5),
    "max_overflow": _int_env("DB_MAX_OVERFLOW", 5),
    # Railway's proxy may drop idle connections; recycle before that happens.
    "pool_recycle": _int_env("DB_POOL_RECYCLE_SECONDS", 1800),
}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    hide_parameters=True,
    **_pool_options,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
