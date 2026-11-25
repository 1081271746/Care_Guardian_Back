def test_health_reports_database(env):
    client, *_ = env
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["database"] == "ok"


def test_private_headers_on_every_response(env):
    client, *_ = env
    response = client.get("/")
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_cors_preflight_allows_configured_origin_only(env):
    client, *_ = env
    allowed = client.options("/patients/", headers={
        "Origin": "http://localhost:4200", "Access-Control-Request-Method": "PATCH"})
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:4200"
    denied = client.options("/patients/", headers={
        "Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in denied.headers


def test_database_errors_are_translated_without_sql(env):
    from sqlalchemy.exc import IntegrityError, OperationalError
    from app.main import app
    client, *_ = env

    def integrity():
        raise IntegrityError("INSERT INTO patients VALUES ('secret-doc')", {}, Exception("dup"))

    def outage():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    app.add_api_route("/__test__/integrity", integrity)
    app.add_api_route("/__test__/outage", outage)
    try:
        conflict = client.get("/__test__/integrity")
        unavailable = client.get("/__test__/outage")
    finally:
        app.router.routes[:] = [r for r in app.router.routes if not getattr(r, "path", "").startswith("/__test__")]
    assert conflict.status_code == 409 and "secret-doc" not in conflict.text
    assert unavailable.status_code == 503 and "refused" not in unavailable.text


def test_openapi_lists_new_endpoints(env):
    client, *_ = env
    paths = client.get("/openapi.json").json()["paths"]
    for path in ("/auth/me", "/dashboard/summary", "/evolution/ai-status",
                 "/evolution/patients/{patient_id}/analyses/{analysis_id}"):
        assert path in paths


def test_published_secret_key_is_refused(monkeypatch):
    import asyncio
    import pytest
    from app.main import app, lifespan
    monkeypatch.setenv("SECRET_KEY", "careguardian_super_secret_key_2026")

    async def start():
        async with lifespan(app):
            pass

    with pytest.raises(RuntimeError, match="publicado"):
        asyncio.run(start())
