"""PostgreSQL-only checks: data survives a new engine (backend restart) and
migrations upgrade a legacy schema without touching existing rows.

Run with TEST_DATABASE_URL pointing to a disposable local database whose name
contains "test" (the CI workflow provides one). Skipped on SQLite.
"""
import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

URL = os.getenv("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not URL or make_url(URL).get_backend_name() != "postgresql",
    reason="Requiere TEST_DATABASE_URL de PostgreSQL local",
)


def test_records_created_through_the_api_survive_a_new_engine(env):
    client, _, pid, headers, _ = env
    created = client.post(f"/notes/patients/{pid}", headers=headers,
                          json={"contenido": "Nota persistente de prueba"})
    assert created.status_code == 201
    note_id = created.json()["id"]
    # A brand-new engine is what a restarted backend process would open.
    fresh = create_engine(URL)
    try:
        with fresh.connect() as connection:
            stored = connection.execute(
                text("SELECT contenido FROM caregiver_notes WHERE id = :id"), {"id": note_id}
            ).scalar()
    finally:
        fresh.dispose()
    assert stored == "Nota persistente de prueba"


def _scratch_database(name):
    admin = create_engine(make_url(URL).set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()
    return make_url(URL).set(database=name).render_as_string(hide_password=False)


def test_migrations_upgrade_legacy_schema_without_losing_rows():
    url = _scratch_database(make_url(URL).database + "_migrations")
    engine = create_engine(url)
    with engine.begin() as connection:
        # Minimal legacy shape: tables created by the original create_all, with data
        # and a duplicated caregiver assignment that must NOT be deleted.
        connection.execute(text("""
            CREATE TABLE users (id SERIAL PRIMARY KEY, nombre VARCHAR(100) NOT NULL,
              email VARCHAR(150) UNIQUE NOT NULL, password_hash VARCHAR(255) NOT NULL,
              rol VARCHAR(30) NOT NULL, activo BOOLEAN NOT NULL, fecha_creacion TIMESTAMPTZ NOT NULL);
            CREATE TABLE patients (id SERIAL PRIMARY KEY, nombres VARCHAR(100) NOT NULL,
              apellidos VARCHAR(100) NOT NULL, fecha_nacimiento DATE NOT NULL,
              documento VARCHAR(30) UNIQUE NOT NULL, telefono VARCHAR(20), direccion VARCHAR(200),
              contacto_emergencia VARCHAR(150), telefono_emergencia VARCHAR(20),
              activo BOOLEAN NOT NULL, fecha_registro TIMESTAMPTZ NOT NULL);
            CREATE TABLE patient_caregivers (id SERIAL PRIMARY KEY,
              patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              rol VARCHAR(50) NOT NULL, fecha_asignacion TIMESTAMPTZ NOT NULL);
            INSERT INTO users VALUES (1, 'Legacy', 'legacy@example.org', 'x', 'cuidador', true, now());
            INSERT INTO patients VALUES (1, 'Legacy', 'Paciente', '1950-01-01', 'LEGACY-1',
              NULL, NULL, NULL, NULL, true, now());
            INSERT INTO patient_caregivers (patient_id, user_id, rol, fecha_asignacion)
              VALUES (1, 1, 'cuidador', now()), (1, 1, 'cuidador', now());
        """))
    environment = {**os.environ, "DATABASE_URL": url}
    for _ in range(2):  # idempotent
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                       env=environment, check=True, capture_output=True)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM patient_caregivers")).scalar() == 2
        assert connection.execute(text("SELECT documento FROM patients")).scalar() == "LEGACY-1"
        indexes = {row[0] for row in connection.execute(text(
            "SELECT indexname FROM pg_indexes WHERE schemaname = 'public'"))}
        assert "ix_symptom_records_patient_id" in indexes
        assert "uq_patient_caregivers_patient_user" not in indexes  # skipped, not forced
        columns = {row[0] for row in connection.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'evolution_analyses'"))}
        assert {"period_start", "period_end", "error"} <= columns
    engine.dispose()
