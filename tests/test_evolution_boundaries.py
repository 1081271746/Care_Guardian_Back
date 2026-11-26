import pytest


@pytest.mark.parametrize("query", [
    "hasta=9999-12-31",
    "desde=0001-01-01&hasta=9999-12-31",
    "desde=2026-11-01&hasta=2026-11-03",
])
def test_inclusive_extreme_and_normal_dates(env, query):
    client, _, pid, headers, _ = env
    result = client.get(f"/evolution/patients/{pid}?{query}", headers=headers)
    assert result.status_code == 200
    assert result.json()["totales"]["sintoma"] == 2


@pytest.mark.parametrize("query", [
    "hasta=not-a-date", "desde=2026-02-30",
    "desde=2026-11-04&hasta=2026-11-01",
])
def test_invalid_periods_are_validation_errors(env, query):
    client, _, pid, headers, _ = env
    assert client.get(f"/evolution/patients/{pid}?{query}", headers=headers).status_code == 422


def test_too_many_records_ask_for_a_shorter_period(env, monkeypatch):
    client, _, pid, headers, _ = env
    monkeypatch.setattr("app.services.evolution.MAX_RECORDS", 1)
    response = client.get(f"/evolution/patients/{pid}", headers=headers)
    assert response.status_code == 422
    assert "período más corto" in response.json()["detail"]
    narrowed = client.get(f"/evolution/patients/{pid}?desde=2026-11-03&hasta=2026-11-03", headers=headers)
    assert narrowed.status_code == 200


def test_metric_points_are_chronological_and_only_real(env):
    client, db, pid, headers, _ = env
    from datetime import datetime, timezone

    from app.models.symptom_record import SymptomRecord
    # A record without pain must not create a pain point (no interpolation).
    db.add(SymptomRecord(patient_id=pid, caregiver_id=1, temperatura=37.0,
                         fecha_registro=datetime(2026, 11, 2, 12, tzinfo=timezone.utc)))
    db.commit()
    metrics = client.get(f"/evolution/patients/{pid}", headers=headers).json()["metricas"]
    pain = metrics["nivel_dolor"]["puntos"]
    assert [p["valor"] for p in pain] == [0, 6]
    assert pain[0]["fecha"] < pain[1]["fecha"]
    assert metrics["temperatura"]["cantidad"] == 3
