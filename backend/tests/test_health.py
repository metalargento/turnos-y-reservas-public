"""Tests del endpoint /health."""


def test_health_ok_when_database_is_up(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "up"}


def test_health_returns_503_without_details_when_database_is_down(client, monkeypatch):
    from utils.db import db
    monkeypatch.setattr(db, "ping", lambda *args, **kwargs: False)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy", "database": "down"}
