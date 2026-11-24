"""Real FastAPI routes and test DB, never production or an external provider."""
from scripts.seed_payloads import DEFAULT_COUNTS
from scripts.seed_runner import run_seed


def test_seed_creates_related_records_through_real_routes_and_survives_rerun(env):
    http, db, _, headers, _ = env

    class TestAPI:
        def request(self, method, path, payload=None):
            response = http.request(method, path, headers=headers,
                                    **({"json": payload} if payload is not None else {}))
            assert response.status_code in (200, 201), f"{method} {path}: {response.status_code}"
            return response.json()

    counts = {key: 2 for key in DEFAULT_COUNTS}
    first = run_seed(TestAPI(), counts, "integration", log=lambda _: None)
    assert all(first[key]["created"] == 2 for key in counts)
    db.expire_all()
    second = run_seed(TestAPI(), counts, "integration", log=lambda _: None)
    assert all(second[key]["created"] == 0 for key in counts)
    assert all(second[key]["verified"] == 2 for key in counts)
    from app.models.patient import Patient
    from app.models.symptom_record import SymptomRecord
    patients = db.query(Patient).filter(Patient.nombres == "Paciente ficticio").all()
    assert len(patients) == 2
    for patient in patients:
        result = http.get(f"/evolution/patients/{patient.id}", headers=headers)
        assert result.status_code == 200
        assert result.json()["totales"] == {
            "sintoma": 1, "medicamento": 1, "cita": 1, "nota": 1, "alerta": 1,
        }
        assert db.query(SymptomRecord).filter_by(patient_id=patient.id).count() == 1
