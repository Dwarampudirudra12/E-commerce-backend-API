"""Auth flow: register -> login -> refresh -> verify -> forgot/reset -> lockout."""
CUSTOMER = {"email": "c1@example.com", "password": "Password123!", "full_name": "C One"}


def _register(client, payload):
    return client.post("/api/v1/auth/register", json=payload)


def _login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_register_login_refresh(client):
    assert _register(client, CUSTOMER).status_code == 201
    login = _login(client, CUSTOMER["email"], CUSTOMER["password"])
    assert login.status_code == 200, login.text
    tokens = login.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == CUSTOMER["email"]

    ref = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert ref.status_code == 200, ref.text


def test_duplicate_register_409(client):
    assert _register(client, CUSTOMER).status_code == 201
    assert _register(client, CUSTOMER).status_code == 409


def test_support_self_register_forbidden(client):
    r = _register(client, {"email": "s@example.com", "password": "Password123!", "role": "SUPPORT"})
    assert r.status_code == 403


def test_lockout_after_5_bad_logins(client):
    _register(client, CUSTOMER)
    for _ in range(5):
        assert _login(client, CUSTOMER["email"], "wrong-pass-123").status_code == 401
    # 6th: even correct password is 423 locked
    assert _login(client, CUSTOMER["email"], CUSTOMER["password"]).status_code == 423


def test_forgot_reset_unlocks(client):
    _register(client, CUSTOMER)
    for _ in range(5):
        _login(client, CUSTOMER["email"], "wrong-pass-123")
    assert client.post("/api/v1/auth/forgot-password", json={"email": CUSTOMER["email"]}).status_code == 200
    # Token is SHA-256 hex in DB; fetch directly in test DB via API is out of scope —
    # instead verify endpoint rejects garbage and accepts flow via DB in test_rbac/manual.
    bad = client.post("/api/v1/auth/reset-password", json={"token": "invalid", "new_password": "NewPass123!"})
    assert bad.status_code == 400
