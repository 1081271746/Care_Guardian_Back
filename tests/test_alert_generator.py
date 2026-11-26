from types import SimpleNamespace

from app.models.alert import Alert
from app.services.alert_generator import generate_alert_from_history


def result(level, score):
    return SimpleNamespace(nivel=level, score=score, tendencias=["Cambio observado"],
                           recomendacion="Seguimiento.")


def test_history_alert_is_reused_and_escalated(env):
    _, db, pid, _, _ = env
    first = generate_alert_from_history(pid, result("medio", 4), db)
    db.commit()
    again = generate_alert_from_history(pid, result("medio", 5), db)
    assert again.id == first.id
    worse = generate_alert_from_history(pid, result("alto", 8), db)
    db.commit()
    assert worse.id == first.id and worse.nivel == "alto"
    assert "8" in worse.mensaje
    calmer = generate_alert_from_history(pid, result("medio", 4), db)
    assert calmer.nivel == "alto"  # never silently downgraded
    assert db.query(Alert).filter_by(patient_id=pid, tipo="evaluacion_historica").count() == 1


def test_low_history_result_creates_nothing(env):
    _, db, pid, _, _ = env
    assert generate_alert_from_history(pid, result("bajo", 1), db) is None


def test_rule_analysis_endpoint_creates_alert_once(env):
    client, db, pid, headers, _ = env
    for values in ({"calidad_sueno": 9, "nivel_dolor": 1}, {"calidad_sueno": 2, "nivel_dolor": 9,
                   "temperatura": 39.3, "apetito": "muy bajo"}):
        client.post(f"/symptoms/patients/{pid}", headers=headers, json=values)
    first = client.get(f"/analysis/patients/{pid}", headers=headers).json()
    second = client.get(f"/analysis/patients/{pid}", headers=headers).json()
    assert first["nivel"] == "alto"
    assert first["alerta_id"] == second["alerta_id"]
