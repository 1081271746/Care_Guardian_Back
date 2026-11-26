from datetime import timedelta

from app.core.time import local_today


def test_summary_counts_only_real_rows_of_assigned_patients(env):
    client, db, pid, headers, other = env
    today = local_today()
    client.post(f"/medications/patients/{pid}", headers=headers, json={
        "nombre": "Med demo", "dosis": "1", "frecuencia": "diaria", "hora": "08:00",
        "fecha_inicio": today.isoformat()})
    client.post(f"/appointments/patients/{pid}", headers=headers, json={
        "titulo": "Control", "especialidad": "General", "profesional": "Dra. Demo",
        "fecha": (today + timedelta(days=3)).isoformat(), "hora": "10:30"})
    client.post(f"/symptoms/patients/{pid}", headers=headers, json={
        "nivel_dolor": 9, "temperatura": 39.2, "nivel_gravedad": "grave"})

    summary = client.get("/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    data = summary.json()
    totals = data["totales"]
    assert totals["pacientes"] == 1
    assert totals["medicamentos_activos"] == 1
    assert totals["citas_proximas"] == 1
    assert totals["sintomas_recientes"] == 1  # the two fixture rows are from Nov 2026 days 1 and 3
    assert totals["alertas_pendientes"] == 1
    assert data["alertas_por_nivel"]["alto"] == 1
    assert sum(day["cantidad"] for day in data["sintomas_por_dia"]) >= 1
    assert len(data["sintomas_por_dia"]) == 14
    assert data["proximas_citas"][0]["hora"] == "10:30"
    assert data["pacientes"][0]["alertas_activas"] == 1
    kinds = {item["tipo"] for item in data["actividad_reciente"]}
    assert {"sintoma", "alerta", "medicamento", "cita"} <= kinds


def test_summary_is_empty_for_caregiver_without_patients(env):
    client, _, _, _, other = env
    data = client.get("/dashboard/summary", headers=other).json()
    assert data["totales"]["pacientes"] == 0
    assert data["actividad_reciente"] == []
    assert all(day["cantidad"] == 0 for day in data["sintomas_por_dia"])


def test_summary_requires_authentication(env):
    client, *_ = env
    response = client.get("/dashboard/summary")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_patient_panel_serializes_patient_and_lists(env):
    client, _, pid, headers, other = env
    panel = client.get(f"/dashboard/patients/{pid}", headers=headers)
    assert panel.status_code == 200
    data = panel.json()
    assert data["patient"]["id"] == pid and "edad" in data["patient"]
    assert data["historical_analysis"]["registros_analizados"] == 2
    assert {"symptoms", "medications", "upcoming_appointments", "recent_notes", "active_alerts"} <= set(data)
    assert client.get(f"/dashboard/patients/{pid}", headers=other).status_code == 403
