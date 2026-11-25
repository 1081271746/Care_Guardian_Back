from datetime import timedelta

import jwt

from app.core import security
from app.core.time import utc_now

PASSWORD = "Segura2026"


def register(client, email="nueva@example.org", password=PASSWORD, nombre="Nueva Cuidadora"):
    return client.post("/users/", json={"nombre": nombre, "email": email, "password": password})


def test_register_login_and_profile(env):
    client, *_ = env
    created = register(client, email="Nueva@Example.org")
    assert created.status_code == 201
    assert created.json()["usuario"]["email"] == "nueva@example.org"
    assert created.json()["usuario"]["rol"] == "cuidador"
    login = client.post("/auth/login", json={"email": "NUEVA@example.org", "password": PASSWORD})
    assert login.status_code == 200
    body = login.json()
    assert body["token_type"] == "bearer" and body["expires_in"] > 0
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "nueva@example.org"
    assert me.json()["pacientes_asignados"] == 0
    assert "password_hash" not in me.text


def test_registration_rejects_duplicates_and_weak_passwords(env):
    client, *_ = env
    assert register(client).status_code == 201
    assert register(client, email="NUEVA@example.org").status_code == 409
    for weak in ("corta1", "solamenteletras", "12345678"):
        assert register(client, email="otra@example.org", password=weak).status_code == 422


def test_registration_ignores_requested_role(env):
    client, *_ = env
    created = client.post("/users/", json={"nombre": "Ana", "email": "ana@example.org",
                                           "password": PASSWORD, "rol": "admin"})
    assert created.status_code == 201
    assert created.json()["usuario"]["rol"] == "cuidador"


def test_registration_can_be_disabled(env, monkeypatch):
    client, *_ = env
    monkeypatch.setenv("ALLOW_PUBLIC_REGISTRATION", "false")
    assert register(client).status_code == 403


def test_login_failures_do_not_reveal_which_part_is_wrong(env):
    client, *_ = env
    register(client)
    wrong_password = client.post("/auth/login", json={"email": "nueva@example.org", "password": "Otra2026"})
    unknown_user = client.post("/auth/login", json={"email": "nadie@example.org", "password": PASSWORD})
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_inactive_user_cannot_log_in(env):
    client, db, *_ = env
    from app.models.user import User
    register(client)
    db.query(User).filter_by(email="nueva@example.org").one().activo = False
    db.commit()
    assert client.post("/auth/login", json={"email": "nueva@example.org", "password": PASSWORD}).status_code == 403


def test_expired_and_tampered_tokens_are_401(env):
    client, *_ = env
    expired = jwt.encode({"sub": "1", "exp": utc_now() - timedelta(minutes=1)},
                         security.SECRET_KEY, algorithm=security.ALGORITHM)
    response = client.get("/patients/", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert "expiró" in response.json()["detail"]
    forged = jwt.encode({"sub": "1", "exp": utc_now() + timedelta(minutes=5)}, "x" * 40, algorithm="HS256")
    assert client.get("/patients/", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
    no_sub = jwt.encode({"exp": utc_now() + timedelta(minutes=5)}, security.SECRET_KEY, algorithm="HS256")
    assert client.get("/patients/", headers={"Authorization": f"Bearer {no_sub}"}).status_code == 401
    assert client.get("/patients/", headers={"Authorization": "Basic abc"}).status_code == 401


def test_deleted_user_token_stops_working(env):
    client, *_ = env
    register(client)
    token = client.post("/auth/login", json={"email": "nueva@example.org", "password": PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/auth/me", headers=headers).json()
    assert client.delete(f"/users/{me['id']}", headers=headers).status_code == 200
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_password_change_requires_current_password(env):
    client, *_ = env
    register(client)
    token = client.post("/auth/login", json={"email": "nueva@example.org", "password": PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user_id = client.get("/auth/me", headers=headers).json()["id"]
    url = f"/users/{user_id}/password"
    assert client.put(url, headers=headers, json={"password_actual": "mala", "password_nueva": "Nueva2027"}).status_code == 400
    assert client.put(url, headers=headers, json={"password_actual": PASSWORD, "password_nueva": "Nueva2027"}).status_code == 200
    assert client.post("/auth/login", json={"email": "nueva@example.org", "password": "Nueva2027"}).status_code == 200
