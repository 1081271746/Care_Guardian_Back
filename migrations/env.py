"""Alembic environment: always uses DATABASE_URL through the app's engine."""
from alembic import context

import app.models  # noqa: F401  (registers every table in Base.metadata)
from app.database.base import Base
from app.database.connection import engine

if context.is_offline_mode():
    raise RuntimeError("Las migraciones se ejecutan en línea contra DATABASE_URL (alembic upgrade head)")

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata,
                      compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
