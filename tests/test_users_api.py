def test_users_can_only_see_and_edit_themselves(env):
    client, _, _, headers, other = env
    assert [u["id"] for u in client.get("/users/", headers=headers).json()] == [1]
    assert client.get("/users/2", headers=headers).status_code == 403
    assert client.put("/users/2", headers=headers, json={"nombre": "Intruso"}).status_code == 403
    assert client.delete("/users/2", headers=headers).status_code == 403
    assert client.put("/users/2/password", headers=headers,
                      json={"password_actual": "x", "password_nueva": "Nueva2027"}).status_code == 403


def test_profile_update_validates_and_detects_duplicate_email(env):
    client, _, _, headers, _ = env
    assert client.put("/users/1", headers=headers, json={"email": "TEST-B@example.org"}).status_code == 409
    assert client.put("/users/1", headers=headers, json={"nombre": " "}).status_code == 422
    updated = client.put("/users/1", headers=headers, json={"nombre": "Cuidadora Ana", "email": "Ana@Example.org"})
    assert updated.status_code == 200
    assert updated.json()["email"] == "ana@example.org"
    assert updated.json()["nombre"] == "Cuidadora Ana"
    assert "password_hash" not in updated.text
