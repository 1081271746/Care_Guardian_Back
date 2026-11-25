from datetime import datetime, timedelta, timezone

from app.core.time import as_utc, local_today

TODAY = local_today()


def med(**extra):
    return {"nombre": "Medicamento demo", "dosis": "1 tableta", "frecuencia": "cada 12 horas",
            "hora": "08:00", "fecha_inicio": TODAY.isoformat(), **extra}


def visit(**extra):
    return {"titulo": "Control", "especialidad": "Medicina general", "profesional": "Dra. Demo",
            "fecha": (TODAY + timedelta(days=2)).isoformat(), "hora": "09:30", **extra}


def test_medications_crud_and_validation(env):
    client, _, pid, headers, _ = env
    base = f"/medications/patients/{pid}"
    assert client.post(base, headers=headers, json=med(hora="8am")).status_code == 422
    assert client.post(base, headers=headers, json=med(nombre=" ")).status_code == 422
    bad_range = med(fecha_fin=(TODAY - timedelta(days=1)).isoformat())
    assert client.post(base, headers=headers, json=bad_range).status_code == 422
    created = client.post(base, headers=headers, json=med(fecha_fin=(TODAY + timedelta(days=10)).isoformat()))
    assert created.status_code == 201
    mid = created.json()["id"]
    assert client.put(f"/medications/{mid}", headers=headers,
                      json={"fecha_inicio": (TODAY + timedelta(days=30)).isoformat()}).status_code == 422
    assert client.put(f"/medications/{mid}", headers=headers, json={"fecha_fin": None}).json()["fecha_fin"] is None
    assert client.delete(f"/medications/{mid}", headers=headers).json()["activo"] is False
    assert client.get(base + "?activos=true", headers=headers).json() == []
    assert len(client.get(base, headers=headers).json()) == 1


def test_appointments_status_dates_and_upcoming(env):
    client, _, pid, headers, _ = env
    base = f"/appointments/patients/{pid}"
    past = visit(fecha=(TODAY - timedelta(days=3)).isoformat())
    assert client.post(base, headers=headers, json=past).status_code == 422
    assert client.post(base, headers=headers, json={**past, "estado": "completada"}).status_code == 201
    assert client.post(base, headers=headers, json=visit(estado="inventado")).status_code == 422
    upcoming = client.post(base, headers=headers, json=visit()).json()
    assert [a["id"] for a in client.get(base + "?proximas=true", headers=headers).json()] == [upcoming["id"]]
    updated = client.put(f"/appointments/{upcoming['id']}", headers=headers, json={"estado": "cancelada"})
    assert updated.json()["estado"] == "cancelada"
    assert client.get(base + "?proximas=true", headers=headers).json() == []
    assert len(client.get(base, headers=headers).json()) == 2


def test_symptoms_validation_alerts_and_backdating(env):
    client, db, pid, headers, _ = env
    base = f"/symptoms/patients/{pid}"
    assert client.post(base, headers=headers, json={}).status_code == 422
    assert client.post(base, headers=headers, json={"nivel_dolor": 11}).status_code == 422
    assert client.post(base, headers=headers, json={"temperatura": 50}).status_code == 422
    assert client.post(base, headers=headers, json={"nivel_dolor": 2, "nivel_gravedad": "terrible"}).status_code == 422
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    assert client.post(base, headers=headers, json={"nivel_dolor": 2, "fecha_registro": future}).status_code == 422
    earlier = (datetime.now(timezone.utc) - timedelta(days=2)).replace(microsecond=0)
    backdated = client.post(base, headers=headers, json={"nivel_dolor": 2, "fecha_registro": earlier.isoformat()})
    assert backdated.status_code == 201
    assert as_utc(datetime.fromisoformat(backdated.json()["fecha_registro"])) == earlier
    severe = client.post(base, headers=headers, json={"nivel_dolor": 9, "temperatura": 39.4, "nivel_gravedad": "grave"})
    assert severe.status_code == 201
    alerts = client.get(f"/alerts/patients/{pid}", headers=headers).json()
    assert [a["symptom_id"] for a in alerts] == [severe.json()["id"]]
    assert alerts[0]["nivel"] == "alto"
    page = client.get(base + "?limit=1", headers=headers).json()
    assert len(page) == 1 and page[0]["id"] == severe.json()["id"]


def test_symptom_correction_reevaluates_risk(env):
    client, _, pid, headers, _ = env
    record = client.post(f"/symptoms/patients/{pid}", headers=headers, json={"nivel_dolor": 1}).json()
    assert client.get(f"/alerts/patients/{pid}", headers=headers).json() == []
    client.put(f"/symptoms/{record['id']}", headers=headers,
               json={"nivel_dolor": 9, "temperatura": 39.5, "nivel_gravedad": "grave"})
    assert len(client.get(f"/alerts/patients/{pid}", headers=headers).json()) == 1


def test_notes_author_rules_and_alerts(env):
    client, db, pid, headers, other = env
    base = f"/notes/patients/{pid}"
    assert client.post(base, headers=headers, json={"contenido": "    "}).status_code == 422
    note = client.post(base, headers=headers, json={
        "contenido": "Hoy no quiso comer, durmió mal y está muy cansado; tiene fiebre."})
    assert note.status_code == 201
    alerts = client.get(f"/alerts/patients/{pid}", headers=headers).json()
    assert alerts and alerts[0]["note_id"] == note.json()["id"]
    client.post(f"/patients/{pid}/caregivers", headers=headers, json={"email": "test-b@example.org"})
    assert client.get(f"/notes/{note.json()['id']}", headers=other).status_code == 200
    assert client.put(f"/notes/{note.json()['id']}", headers=other, json={"contenido": "Cambio ajeno"}).status_code == 403
    assert client.delete(f"/notes/{note.json()['id']}", headers=other).status_code == 403
    assert client.delete(f"/notes/{note.json()['id']}", headers=headers).status_code == 200
    assert client.get(base, headers=headers).json() == []


def test_alert_lifecycle_and_duplicates(env):
    client, _, pid, headers, _ = env
    base = f"/alerts/patients/{pid}"
    payload = {"titulo": "Caída leve en el baño", "mensaje": "Se observó una caída sin golpe aparente.", "nivel": "alto"}
    assert client.post(base, headers=headers, json={**payload, "origen": "sistema"}).status_code == 422
    assert client.post(base, headers=headers, json={**payload, "nivel": "critico"}).status_code == 422
    created = client.post(base, headers=headers, json=payload)
    assert created.status_code == 201 and created.json()["origen"] == "manual"
    assert client.post(base, headers=headers, json={**payload, "titulo": "CAÍDA LEVE EN EL BAÑO"}).status_code == 409
    aid = created.json()["id"]
    closed = client.put(f"/alerts/{aid}", headers=headers, json={"estado": "atendida"}).json()
    assert closed["activa"] is False
    assert client.get(base, headers=headers).json() == []
    history = client.get(base + "?incluir_cerradas=true", headers=headers).json()
    assert [a["estado"] for a in history] == ["atendida"]
    reopened = client.put(f"/alerts/{aid}", headers=headers, json={"estado": "en_revision"}).json()
    assert reopened["activa"] is True
    assert client.get(base + "?nivel=alto", headers=headers).json()[0]["id"] == aid
    assert client.delete(f"/alerts/{aid}", headers=headers).status_code == 200
    assert client.get(f"/alerts/{aid}", headers=headers).json()["estado"] == "descartada"


def test_rescheduling_a_pending_visit_into_the_past_is_rejected(env):
    client, _, pid, headers, _ = env
    created = client.post(f"/appointments/patients/{pid}", headers=headers, json=visit()).json()
    url = f"/appointments/{created['id']}"
    yesterday = (TODAY - timedelta(days=1)).isoformat()
    assert client.put(url, headers=headers, json={"fecha": yesterday}).status_code == 422
    done = client.put(url, headers=headers, json={"fecha": yesterday, "estado": "completada"})
    assert done.status_code == 200 and done.json()["estado"] == "completada"
