from datetime import datetime, timedelta, timezone

from app.services.evolution import utc


def test_naive_legacy_timestamps_are_interpreted_as_utc():
    value = datetime(2026, 11, 1, 12)
    assert utc(value).isoformat() == "2026-11-01T12:00:00+00:00"


def test_offsets_are_normalized_before_timeline_sorting():
    local = datetime(2026, 11, 1, 8, tzinfo=timezone(timedelta(hours=-5)))
    earlier = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
    assert utc(local).isoformat() > utc(earlier).isoformat()
    assert utc(local).hour == 13
    assert utc(utc(local)) == utc(local)


def test_period_days_follow_caregiver_timezone(env, monkeypatch):
    """21:30 in Bogotá on Nov 10 is 02:30 UTC on Nov 11 but belongs to Nov 10."""
    from app.models.symptom_record import SymptomRecord
    client, db, pid, headers, _ = env
    monkeypatch.setenv("APP_TIMEZONE", "America/Bogota")
    db.add(SymptomRecord(patient_id=pid, caregiver_id=1, nivel_dolor=4,
                         fecha_registro=datetime(2026, 11, 11, 2, 30, tzinfo=timezone.utc)))
    db.commit()
    url = f"/evolution/patients/{pid}"
    day_10 = client.get(url + "?desde=2026-11-10&hasta=2026-11-10", headers=headers).json()
    day_11 = client.get(url + "?desde=2026-11-11&hasta=2026-11-11", headers=headers).json()
    assert day_10["totales"]["sintoma"] == 1
    assert day_11["totales"]["sintoma"] == 0
    assert day_10["zona_horaria"] == "America/Bogota"


def test_appointment_hour_is_local_wall_clock(env, monkeypatch):
    from datetime import date, time
    from app.models.appointment import Appointment
    client, db, pid, headers, _ = env
    monkeypatch.setenv("APP_TIMEZONE", "America/Bogota")
    db.add(Appointment(patient_id=pid, titulo="Control", especialidad="General",
                       profesional="Demo", fecha=date(2026, 11, 20), hora=time(9, 0)))
    db.commit()
    events = client.get(f"/evolution/patients/{pid}", headers=headers).json()["historial"]
    visit = next(e for e in events if e["tipo"] == "cita")
    # 09:00 in Bogotá (UTC-5) is 14:00 UTC.
    assert visit["fecha"] == "2026-11-20T14:00:00+00:00"
