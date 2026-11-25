NEW = {"nombres": "Rosa", "apellidos": "Demo", "fecha_nacimiento": "1948-03-02", "documento": "DEMO-ROSA"}


def test_create_validates_and_rejects_duplicates(env):
    client, _, _, headers, _ = env
    assert client.post("/patients/", headers=headers, json={**NEW, "nombres": "   "}).status_code == 422
    assert client.post("/patients/", headers=headers, json={**NEW, "fecha_nacimiento": "2999-01-01"}).status_code == 422
    assert client.post("/patients/", headers=headers, json={**NEW, "telefono": "llámame"}).status_code == 422
    assert client.post("/patients/", headers=headers, json={**NEW, "documento": "a b"}).status_code == 422
    created = client.post("/patients/", headers=headers, json={**NEW, "telefono": ""})
    assert created.status_code == 201
    assert created.json()["telefono"] is None
    assert created.json()["edad"] >= 77
    assert client.post("/patients/", headers=headers, json=NEW).status_code == 409


def test_list_is_sorted_and_filterable(env):
    client, _, pid, headers, _ = env
    client.post("/patients/", headers=headers, json=NEW)
    names = [p["apellidos"] for p in client.get("/patients/", headers=headers).json()]
    assert names == sorted(names)
    found = client.get("/patients/?q=rosa", headers=headers).json()
    assert [p["documento"] for p in found] == ["DEMO-ROSA"]
    assert client.get("/patients/?q=DEMO-ROSA", headers=headers).json()[0]["nombres"] == "Rosa"


def test_update_clears_optional_fields_and_protects_document(env):
    client, _, pid, headers, _ = env
    other = client.post("/patients/", headers=headers, json=NEW).json()
    url = f"/patients/{pid}"
    assert client.put(url, headers=headers, json={"direccion": "Calle demo 1"}).json()["direccion"] == "Calle demo 1"
    assert client.put(url, headers=headers, json={"direccion": None}).json()["direccion"] is None
    assert client.put(url, headers=headers, json={"documento": other["documento"]}).status_code == 409
    assert client.put(url, headers=headers, json={"nombres": None}).status_code == 422
    assert client.put(url, headers=headers, json={"desconocido": 1}).status_code == 422


def test_delete_deactivates_and_keeps_history(env):
    client, db, pid, headers, _ = env
    from app.models.symptom_record import SymptomRecord
    before = db.query(SymptomRecord).filter_by(patient_id=pid).count()
    deleted = client.delete(f"/patients/{pid}", headers=headers)
    assert deleted.status_code == 200 and deleted.json()["activo"] is False
    assert client.get(f"/patients/{pid}", headers=headers).json()["activo"] is False
    assert db.query(SymptomRecord).filter_by(patient_id=pid).count() == before
    # Inactive patients are read-only for new clinical records.
    assert client.post(f"/notes/patients/{pid}", headers=headers, json={"contenido": "No debería guardarse"}).status_code == 400
    assert client.put(f"/patients/{pid}", headers=headers, json={"activo": True}).json()["activo"] is True


def test_caregiver_assignment_by_email_and_removal(env):
    client, db, pid, headers, other = env
    url = f"/patients/{pid}/caregivers"
    assert client.post(url, headers=headers, json={"email": "nadie@example.org"}).status_code == 404
    assert client.post(url, headers=headers, json={}).status_code == 422
    assert client.post(url, headers=headers, json={"email": "TEST-B@example.org", "rol": "familiar"}).status_code == 201
    assert client.post(url, headers=headers, json={"email": "test-b@example.org"}).status_code == 409
    team = client.get(url, headers=headers).json()
    assert [member["rol"] for member in team] == ["cuidador", "familiar"]
    # The new caregiver now has access.
    assert client.get(f"/patients/{pid}", headers=other).status_code == 200
    b_id = team[1]["user_id"]
    assert client.delete(f"{url}/{b_id}", headers=headers).status_code == 200
    assert client.get(f"/patients/{pid}", headers=other).status_code == 403
    a_id = team[0]["user_id"]
    assert client.delete(f"{url}/{a_id}", headers=headers).status_code == 409


def test_other_caregiver_cannot_touch_patient(env):
    client, _, pid, _, other = env
    url = f"/patients/{pid}"
    assert client.get(url, headers=other).status_code == 403
    assert client.put(url, headers=other, json={"nombres": "X"}).status_code == 403
    assert client.delete(url, headers=other).status_code == 403
    assert client.get(f"{url}/caregivers", headers=other).status_code == 403
    assert client.get("/patients/999999", headers=other).status_code == 403


def test_inactive_patient_records_are_read_only(env):
    client, db, pid, headers, _ = env
    from app.models.symptom_record import SymptomRecord
    record = db.query(SymptomRecord).filter_by(patient_id=pid).first()
    client.delete(f"/patients/{pid}", headers=headers)
    assert client.get(f"/symptoms/{record.id}", headers=headers).status_code == 200
    assert client.put(f"/symptoms/{record.id}", headers=headers, json={"nivel_dolor": 3}).status_code == 400


def test_alerts_can_still_be_closed_after_deactivation(env):
    client, _, pid, headers, _ = env
    alert = client.post(f"/alerts/patients/{pid}", headers=headers,
                        json={"titulo": "Pendiente al cerrar", "mensaje": "Alerta previa a la baja"}).json()
    client.delete(f"/patients/{pid}", headers=headers)
    closed = client.put(f"/alerts/{alert['id']}", headers=headers, json={"estado": "atendida"})
    assert closed.status_code == 200 and closed.json()["activa"] is False
