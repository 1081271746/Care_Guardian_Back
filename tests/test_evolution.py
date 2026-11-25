import json
import os
import subprocess
import sys
from datetime import date, datetime, time, timezone
from unittest.mock import patch
import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.database.base import Base
from app.models.patient import Patient
from app.models.evolution_analysis import EvolutionAnalysis
from app.models.medication import Medication
from app.models.appointment import Appointment
from app.models.symptom_record import SymptomRecord
from app.models.caregiver_note import CaregiverNote
from app.models.alert import Alert
from app.services.groq_analysis import GROQ_URL

BODY = {"consentimiento": True, "version_consentimiento": "groq-minimized-v1"}

@pytest.mark.parametrize("path", ["/patients/not-a-number", "/medications/not-a-number",
                                 "/evolution/patients/not-a-number"])
def test_invalid_path_ids_are_validation_errors(env, path):
    client, _, _, headers, _ = env
    assert client.get(path, headers=headers).status_code == 422


def test_real_metrics_zero_values_filters_and_empty(env):
    client, db, pid, headers, _ = env
    url = f"/evolution/patients/{pid}"
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["metricas"]["nivel_dolor"]["promedio"] == 3
    assert data["metricas"]["nivel_dolor"]["cambio"] == 6
    assert data["totales"]["sintoma"] == 2
    assert data["historial"][0]["fecha"] > data["historial"][1]["fecha"]
    assert response.headers["cache-control"] == "private, no-store"
    filtered = client.get(url + "?desde=2026-11-03&hasta=2026-11-03", headers=headers).json()
    assert filtered["totales"]["sintoma"] == 1
    assert not filtered["datos_suficientes"]
    empty = client.get(url + "?desde=2030-01-01", headers=headers).json()
    assert not empty["historial"]
    assert empty["metricas"]["nivel_dolor"]["promedio"] is None
    assert client.get(url+"?desde=2026-12-01&hasta=2026-01-01", headers=headers).status_code == 422


@pytest.mark.parametrize("suffix", ["", "/analyses"])
def test_evolution_isolation(env, suffix):
    client, _, pid, headers, other = env
    url = f"/evolution/patients/{pid}{suffix}"
    assert client.get(url).status_code in (401, 403)
    assert client.get(url, headers=other).status_code == 403
    assert client.post(f"/evolution/patients/{pid}/analyses", json=BODY, headers=other).status_code == 403


def test_consent_insufficient_and_configuration(env, monkeypatch):
    client, _, pid, headers, _ = env
    url = f"/evolution/patients/{pid}/analyses"
    for body in ({}, {**BODY, "consentimiento": False}, {**BODY, "version_consentimiento": "old"}):
        assert client.post(url, json=body, headers=headers).status_code == 422
    assert client.post(url, json={**BODY, "desde": "2030-01-01"}, headers=headers).status_code == 422
    monkeypatch.delenv("GROQ_API_KEY")
    assert client.post(url, json=BODY, headers=headers).status_code == 503
    assert client.get(f"/evolution/patients/{pid}", headers=headers).status_code == 200


def response(content, status=200):
    return httpx.Response(status, request=httpx.Request("POST", GROQ_URL),
                          json={"choices": [{"message": {"content": content}}]})


def test_groq_success_minimization_history_and_quota(env, monkeypatch):
    client, db, pid, headers, _ = env
    monkeypatch.setenv("GROQ_REQUESTS_PER_MINUTE", "1")
    url = f"/evolution/patients/{pid}/analyses"
    with patch("app.services.groq_analysis.GroqHTTPClient.post", return_value=response('{"resumen":["nivel_dolor"],"revisar":[]}')) as post:
        result = client.post(url, json=BODY, headers=headers)
        assert result.status_code == 201
        payload = json.dumps(post.call_args.kwargs["json"], ensure_ascii=False)
        assert "PRIVATE-FREE-TEXT" not in payload
        assert "Paciente prueba" not in payload
        assert "patient_id" not in payload
        assert "documento" not in payload
        assert "2026-11-01" not in payload
        assert client.post(url, json=BODY, headers=headers).status_code == 429
        assert post.call_count == 1
    saved = client.get(url, headers=headers).json()
    assert len(saved) == 1
    assert "Dolor:" in saved[0]["resultado"]["resumen"][0]
    assert db.query(EvolutionAnalysis).one().consent_version == BODY["version_consentimiento"]


@pytest.mark.parametrize("content", ['not json', '{"resumen":["inventado"],"revisar":[]}',
    '{"resumen":[],"revisar":[]}', '{"resumen":["nivel_dolor"],"revisar":[],"diagnostico":"x"}'])
def test_invalid_ai_is_not_saved(env, content):
    client, db, pid, headers, _ = env
    with patch("app.services.groq_analysis.GroqHTTPClient.post", return_value=response(content)):
        result = client.post(f"/evolution/patients/{pid}/analyses", json=BODY, headers=headers)
    assert result.status_code == 502
    assert db.query(EvolutionAnalysis).one().status == "failed"
    assert client.get(f"/evolution/patients/{pid}/analyses", headers=headers).json() == []


@pytest.mark.parametrize("error,expected", [
    (httpx.ReadTimeout("timeout"), 504), (httpx.ConnectError("connection"), 502),
])
def test_groq_unavailable(env, error, expected):
    client, _, pid, headers, _ = env
    with patch("app.services.groq_analysis.GroqHTTPClient.post", side_effect=error):
        assert client.post(f"/evolution/patients/{pid}/analyses", json=BODY, headers=headers).status_code == expected
    assert client.get(f"/evolution/patients/{pid}", headers=headers).status_code == 200


@pytest.mark.parametrize("status,expected", [(401, 502), (429, 503), (500, 502)])
def test_provider_http_errors(env, status, expected):
    client, _, pid, headers, _ = env
    with patch("app.services.groq_analysis.GroqHTTPClient.post", return_value=response("", status)):
        assert client.post(f"/evolution/patients/{pid}/analyses", json=BODY, headers=headers).status_code == expected


@pytest.mark.parametrize("resource", ["patients", "medications/patients", "appointments/patients"])
def test_legacy_collection_isolation(env, resource):
    client, _, pid, _, other = env
    assert client.get(f"/{resource}/{pid}", headers=other).status_code == 403
    assert client.get("/patients/", headers=other).json() == []


def test_assignments_cannot_be_self_granted(env):
    client, _, pid, _, other = env
    assert client.post(f"/patients/{pid}/caregivers", headers=other, json={"user_id": 2}).status_code == 403


def test_new_patient_auto_assignment(env):
    client, _, _, headers, other = env
    result = client.post("/patients/", headers=headers, json={
        "nombres": "Nuevo", "apellidos": "Prueba", "documento": "TEST-NEW", "fecha_nacimiento": "1950-01-01"
    })
    assert result.status_code == 201
    new_id = result.json()["id"]
    assert client.get(f"/evolution/patients/{new_id}", headers=headers).status_code == 200
    assert client.get(f"/evolution/patients/{new_id}", headers=other).status_code == 403


def test_user_access_and_role_escalation(env):
    client, _, _, headers, other = env
    assert client.put("/users/1", json={"rol": "admin"}, headers=headers).status_code == 403
    assert client.get("/users/1").status_code in (401, 403)
    assert client.get("/users/1", headers=other).status_code == 403


def test_non_destructive_migrations(tmp_path):
    database = tmp_path / "migrations.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{database}"}
    # Start from an original deployment: table already exists and contains a row.
    engine = create_engine(env["DATABASE_URL"])
    Base.metadata.create_all(
        engine, tables=[t for t in Base.metadata.sorted_tables if t.name != "evolution_analyses"]
    )
    with Session(engine) as db:
        db.add(Patient(nombres="Migración", apellidos="Prueba", documento="TEST-MIGRATION",
                       fecha_nacimiento=date(1950, 1, 1)))
        db.commit()
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE legacy_marker (id INTEGER PRIMARY KEY, value TEXT)"))
        connection.execute(text("INSERT INTO legacy_marker VALUES (1, 'preserve')"))
    for _ in range(2):
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=env, check=True, capture_output=True)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT value FROM legacy_marker")).scalar() == "preserve"
        assert connection.execute(text("SELECT documento FROM patients")).scalar() == "TEST-MIGRATION"
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar() == "002_evolution"


@pytest.mark.parametrize("kind", ["medications", "appointments", "symptoms", "notes", "alerts"])
def test_legacy_objects_reject_other_caregivers(env, kind):
    client, db, pid, headers, other = env
    if kind == "medications":
        record = Medication(patient_id=pid, nombre="Prueba", dosis="1", frecuencia="diaria",
                            hora="08:00", fecha_inicio=date(2026, 11, 1))
    elif kind == "appointments":
        record = Appointment(patient_id=pid, titulo="Prueba", especialidad="Prueba",
                             profesional="Prueba", fecha=date(2026, 11, 1), hora=time(8))
    elif kind == "notes":
        record = CaregiverNote(patient_id=pid, caregiver_id=1, contenido="Solo para pruebas")
    elif kind == "alerts":
        record = Alert(patient_id=pid, tipo="manual", nivel="bajo", titulo="Prueba", mensaje="Solo para pruebas")
    else:
        record = db.query(SymptomRecord).first()
    db.add(record); db.commit()
    url = f"/{kind}/{record.id}"
    assert client.get(url, headers=headers).status_code == 200
    assert client.get(url, headers=other).status_code == 403
    assert client.put(url, headers=other, json={}).status_code == 403
    assert client.delete(url, headers=other).status_code == 403
