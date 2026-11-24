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
