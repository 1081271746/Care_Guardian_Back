import os
import secrets
from datetime import date, datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", secrets.token_urlsafe(48))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database.base import Base
from app.database.connection import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.patient_caregiver import PatientCaregiver
from app.models.symptom_record import SymptomRecord
from app.core.security import create_access_token, hash_password

class AuthHeaders(dict):
    def __repr__(self):
        return "{'Authorization': '[REDACTED]'}"


@pytest.fixture
def env(monkeypatch):
    # This optional URL must point to an expendable LOCAL database, never production.
    url = os.getenv("TEST_DATABASE_URL", "sqlite://")
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite" and (
        parsed.host not in {"localhost", "127.0.0.1", "::1"}
        or "test" not in (parsed.database or "").lower()
    ):
        raise RuntimeError("TEST_DATABASE_URL debe ser una base local desechable con 'test' en su nombre")
    engine = create_engine(url, **(
        {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
        if url.startswith("sqlite") else {}
    ))
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        a = User(nombre="Cuidador prueba", email="test-a@example.org", password_hash=hash_password(secrets.token_urlsafe()))
        b = User(nombre="Otro cuidador", email="test-b@example.org", password_hash=hash_password(secrets.token_urlsafe()))
        db.add_all([a, b]); db.flush()
        p = Patient(nombres="Paciente prueba", apellidos="Prueba", fecha_nacimiento=date(1950, 1, 1), documento="TEST-ONLY")
        db.add(p); db.flush()
        db.add(PatientCaregiver(patient_id=p.id, user_id=a.id))
        for day, pain in [(1, 0), (3, 6)]:
            db.add(SymptomRecord(
                patient_id=p.id, caregiver_id=a.id, nivel_dolor=pain, calidad_sueno=8-day,
                temperatura=36.5, observaciones="PRIVATE-FREE-TEXT",
                fecha_registro=datetime(2026, 11, day, 12, tzinfo=timezone.utc),
            ))
        db.commit()
        def override_db():
            yield db
        app.dependency_overrides[get_db] = override_db
        headers = AuthHeaders(Authorization="Bearer " + create_access_token({"sub": str(a.id)}))
        other = AuthHeaders(Authorization="Bearer " + create_access_token({"sub": str(b.id)}))
        monkeypatch.setenv("GROQ_API_KEY", secrets.token_urlsafe())
        monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")
        with TestClient(app) as client:
            yield client, db, p.id, headers, other
        app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()
