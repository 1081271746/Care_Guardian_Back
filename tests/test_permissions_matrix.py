"""Every patient-scoped route must answer 401 without a token and 403 to a
caregiver who is not assigned to the patient, without revealing data."""
import pytest

COLLECTIONS = ["medications", "appointments", "symptoms", "notes", "alerts", "dashboard",
               "analysis", "evolution"]


@pytest.mark.parametrize("resource", COLLECTIONS)
def test_collections_require_authentication(env, resource):
    client, _, pid, _, _ = env
    assert client.get(f"/{resource}/patients/{pid}").status_code == 401


@pytest.mark.parametrize("resource", COLLECTIONS)
def test_collections_are_isolated_between_caregivers(env, resource):
    client, _, pid, _, other = env
    response = client.get(f"/{resource}/patients/{pid}", headers=other)
    assert response.status_code == 403
    assert "PRIVATE-FREE-TEXT" not in response.text


@pytest.mark.parametrize("resource,payload", [
    ("medications", {"nombre": "x", "dosis": "x", "frecuencia": "x", "hora": "08:00", "fecha_inicio": "2026-11-01"}),
    ("appointments", {"titulo": "x", "especialidad": "x", "profesional": "x", "fecha": "2030-01-01", "hora": "08:00"}),
    ("symptoms", {"nivel_dolor": 1}),
    ("notes", {"contenido": "Intento ajeno"}),
    ("alerts", {"titulo": "Intento", "mensaje": "Intento ajeno"}),
])
def test_other_caregiver_cannot_create_records(env, resource, payload):
    client, db, pid, _, other = env
    assert client.post(f"/{resource}/patients/{pid}", headers=other, json=payload).status_code == 403


def test_unknown_patient_is_forbidden_not_found(env):
    """Do not disclose whether a patient id exists for someone else."""
    client, _, _, headers, _ = env
    assert client.get("/medications/patients/999999", headers=headers).status_code == 403


def test_list_of_patients_only_contains_assigned(env):
    client, _, pid, headers, other = env
    assert [p["id"] for p in client.get("/patients/", headers=headers).json()] == [pid]
    assert client.get("/patients/", headers=other).json() == []
    assert client.get("/users/", headers=other).json()[0]["email"] == "test-b@example.org"
