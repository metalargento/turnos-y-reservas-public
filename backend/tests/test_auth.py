"""Tests de registro, login y rutas protegidas."""

VALID_USER = {
    "email": "ana@example.com",
    "password": "Str0ngPassword",
    "full_name": "Ana Test",
    "role": "owner",
}


def test_register_returns_tokens(client, ip_headers):
    response = client.post("/api/auth/register", json=VALID_USER, headers=ip_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]


def test_register_duplicate_email_returns_409(client, ip_headers):
    client.post("/api/auth/register", json=VALID_USER, headers=ip_headers)
    response = client.post("/api/auth/register", json=VALID_USER, headers=ip_headers)
    assert response.status_code == 409


def test_register_rejects_weak_password(client, ip_headers):
    response = client.post("/api/auth/register", json={**VALID_USER, "password": "alllowercase1"}, headers=ip_headers)
    assert response.status_code == 422


def test_login_success(client, ip_headers):
    client.post("/api/auth/register", json=VALID_USER, headers=ip_headers)
    response = client.post(
        "/api/auth/login",
        json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
        headers=ip_headers,
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_wrong_password_returns_401(client, ip_headers):
    client.post("/api/auth/register", json=VALID_USER, headers=ip_headers)
    response = client.post(
        "/api/auth/login",
        json={"email": VALID_USER["email"], "password": "WrongPassword1"},
        headers=ip_headers,
    )
    assert response.status_code == 401


def test_login_unknown_user_returns_401(client, ip_headers):
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "Whatever123"},
        headers=ip_headers,
    )
    assert response.status_code == 401


def test_me_requires_token_and_works_with_it(client, ip_headers):
    assert client.get("/api/auth/me").status_code == 401

    token = client.post("/api/auth/register", json=VALID_USER, headers=ip_headers).json()["access_token"]
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == VALID_USER["email"]


def test_login_is_rate_limited(client, ip_headers, monkeypatch):
    from config.settings import settings
    monkeypatch.setattr(settings, "auth_rate_limit", "3/minute")
    payload = {"email": "nobody@example.com", "password": "Whatever123"}

    codes = [client.post("/api/auth/login", json=payload, headers=ip_headers).status_code for _ in range(4)]

    assert codes == [401, 401, 401, 429]
