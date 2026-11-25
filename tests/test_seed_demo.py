import json
from datetime import date
import httpx
import pytest
from app.schemas.patient import PatientCreate
from app.schemas.medication import MedicationCreate
from app.schemas.appointment import AppointmentCreate
from app.schemas.symptom_record import SymptomRecordCreate
from app.schemas.caregiver_note import CaregiverNoteCreate
from app.schemas.alert import AlertCreate
from scripts.seed_demo import main
from scripts.seed_http import SeedClient, SeedError, validate_url
from scripts.seed_payloads import DEFAULT_COUNTS, patient_payload, resource_payload
from scripts.seed_runner import run_seed


def test_fixtures_match_existing_schemas_and_document_column():
    patient = patient_payload("a" * 24, 999)
    PatientCreate.model_validate(patient)
    assert len(patient["documento"]) <= 30
    assert patient == patient_payload("a" * 24, 999)
    assert patient != patient_payload("other", 999)
    for name, schema in [
        ("medications", MedicationCreate), ("appointments", AppointmentCreate),
        ("symptoms", SymptomRecordCreate), ("notes", CaregiverNoteCreate), ("alerts", AlertCreate),
    ]:
        schema.model_validate(resource_payload("test", name, 0, date(2026, 11, 1)))


@pytest.mark.parametrize("url", ["http://example.org", "https://u:p@example.org",
                                     "https://example.org?token=unsafe", "file:///tmp/db", ""])
def test_seed_rejects_unsafe_destinations(url):
    with pytest.raises(SeedError):
        validate_url(url)


def test_dry_run_needs_no_credentials_or_network(monkeypatch, capsys):
    monkeypatch.delenv("SEED_PASSWORD", raising=False)
    assert main([]) == 0
    assert json.loads(capsys.readouterr().out)["mode"] == "dry-run"
    assert main(["--patients", "0"]) == 1
    assert main(["--symptoms", "-1"]) == 1


def test_remote_apply_requires_confirmation(monkeypatch):
    monkeypatch.setenv("SEED_BASE_URL", "https://example.org")
    assert main(["--apply"]) == 1


def test_http_client_renews_once_and_does_not_leak_response_bodies():
    calls = []
    def handle(request):
        calls.append(request.url.path)
        if request.url.path == "/auth/login":
            return httpx.Response(200, json={"access_token": "test-only-not-a-real-token"})
        return httpx.Response(401, json={"detail": "SENSITIVE-RESPONSE"})
    client = SeedClient("https://example.org", "test@example.org", "test-only",
                        transport=httpx.MockTransport(handle))
    try:
        with pytest.raises(SeedError) as caught:
            client.request("GET", "/patients/")
        assert "SENSITIVE" not in str(caught.value)
        assert calls == ["/auth/login", "/patients/", "/auth/login", "/patients/"]
    finally:
        client.close()


def test_seed_rerun_uses_remote_records_and_readback():
    # An HTTP mock only for this unit test; the real runner uses the deployed API.
    storage = {"/patients/": []}
    writes = []
    def handle(request):
        path = request.url.path
        if path == "/auth/login":
            return httpx.Response(200, json={"access_token": "test-only"})
        if path.endswith("/caregivers"):
            return httpx.Response(200, json=[{"user_id": 1}])
        rows = storage.setdefault(path, [])
        if request.method == "POST":
            record = json.loads(request.content)
            record["id"] = len(rows) + 1
            if path != "/patients/":
                record["patient_id"] = int(path.rsplit("/", 1)[-1])
            rows.append(record)
            writes.append(path)
            return httpx.Response(200, json=record)
        return httpx.Response(200, json=rows)
    client = SeedClient("https://example.org", "test@example.org", "test-only",
                        transport=httpx.MockTransport(handle))
    counts = {key: 2 for key in DEFAULT_COUNTS}
    try:
        first = run_seed(client, counts, "test", log=lambda _: None)
        assert all(first[key]["created"] == 2 for key in counts)
        count = len(writes)
        second = run_seed(client, counts, "test", log=lambda _: None)
        assert len(writes) == count
        assert all(second[key]["existing"] == second[key]["verified"] == 2 for key in counts)
    finally:
        client.close()


def test_ambiguous_post_transport_failure_is_not_retried():
    count = 0
    def handle(request):
        nonlocal count
        if request.url.path == "/auth/login":
            return httpx.Response(200, json={"access_token": "test-only"})
        count += 1
        raise httpx.ReadTimeout("do not expose request")
    client = SeedClient("https://example.org", "test@example.org", "test-only",
                        transport=httpx.MockTransport(handle))
    try:
        with pytest.raises(SeedError):
            client.request("POST", "/patients/", {})
        assert count == 1
    finally:
        client.close()


def test_demo_records_are_labelled_spread_in_time_and_never_future():
    from datetime import datetime, timezone
    now = datetime(2026, 11, 25, 15, tzinfo=timezone.utc)
    stamps = set()
    for index in range(40):
        symptom = resource_payload("t", "symptoms", index, date(2026, 11, 25), now)
        assert symptom["observaciones"].startswith("CG-DEMO-t-symptoms-")
        moment = datetime.fromisoformat(symptom["fecha_registro"])
        assert moment < now
        stamps.add(moment.date())
    assert len(stamps) >= 14  # enough distinct days for the Evolución charts
    assert "(demo)" in patient_payload("t", 0)["nombres"]
    assert "(demo)" in resource_payload("t", "medications", 0)["nombre"]
    assert "(demo)" in resource_payload("t", "alerts", 0)["titulo"]


def test_create_account_registers_only_when_login_fails():
    calls = []
    def handle(request):
        calls.append((request.method, request.url.path))
        if request.url.path == "/auth/login":
            return httpx.Response(401 if len(calls) == 1 else 200, json={"access_token": "test-only"})
        if request.url.path == "/users/":
            body = json.loads(request.content)
            assert body["email"] == "demo@example.org" and "rol" not in body
            return httpx.Response(201, json={"usuario": {"id": 1}})
        return httpx.Response(404)
    client = SeedClient("https://example.org", "demo@example.org", "Demo2026",
                        transport=httpx.MockTransport(handle))
    try:
        assert client.ensure_account("Demo") == "created"
        assert client.ensure_account("Demo") == "existing"
        assert ("POST", "/users/") in calls and calls.count(("POST", "/users/")) == 1
    finally:
        client.close()
