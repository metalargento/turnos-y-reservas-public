"""
Configuración de pytest.

Los tests usan una base PostgreSQL aislada indicada por TEST_DATABASE_URL. Por seguridad
solo corren si el nombre de la base termina en `_test`, para no tocar datos reales.
"""
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import psycopg2
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")

if TEST_DATABASE_URL:
    db_name = urlparse(TEST_DATABASE_URL).path.lstrip("/")
    if not db_name.endswith("_test"):
        raise RuntimeError("TEST_DATABASE_URL debe apuntar a una base cuyo nombre termine en '_test'")
    # Deben definirse antes de importar la app (settings se lee al importar)
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["SECRET_KEY"] = "test-secret-key-only-for-automated-tests-0000"
    os.environ["JWT_SECRET"] = "test-jwt-secret-only-for-automated-tests-0000"
    os.environ["APP_ENV"] = "test"
    os.environ["RESEND_API_KEY"] = ""
    os.environ["AUTH_RATE_LIMIT"] = "1000/minute"

TZ_AR = ZoneInfo("America/Argentina/Buenos_Aires")


def pytest_collection_modifyitems(config, items):
    """Sin TEST_DATABASE_URL se omiten todos los tests, con un motivo claro."""
    if TEST_DATABASE_URL:
        return
    skip = pytest.mark.skip(reason="Definí TEST_DATABASE_URL (base PostgreSQL de pruebas, nombre terminado en _test)")
    for item in items:
        item.add_marker(skip)


def _ensure_database_exists() -> None:
    """Crea la base de pruebas si no existe (conectando a la base administrativa 'postgres')."""
    parsed = urlparse(TEST_DATABASE_URL)
    name = parsed.path.lstrip("/")
    admin_url = TEST_DATABASE_URL.replace(f"/{name}", "/postgres", 1)
    conn = psycopg2.connect(admin_url)
    conn.autocommit = True
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{name}"')
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Crea la base de pruebas si hace falta y aplica las migraciones una vez por sesión."""
    _ensure_database_exists()
    from migrations.run_migrations import run_migrations
    run_migrations()


@pytest.fixture(autouse=True)
def clean_tables(migrated_database):
    """Deja las tablas vacías antes de cada test."""
    conn = psycopg2.connect(TEST_DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("TRUNCATE users, businesses RESTART IDENTITY CASCADE")
    conn.close()
    yield


@pytest.fixture(autouse=True)
def no_real_emails(monkeypatch):
    """Evita enviar emails reales: reemplaza los envíos por funciones vacías."""
    from integrations.resend_service import resend_service
    monkeypatch.setattr(resend_service, "send_booking_confirmation", lambda **kwargs: True)
    monkeypatch.setattr(resend_service, "send_booking_cancellation", lambda **kwargs: True)


@pytest.fixture
def client():
    """Cliente HTTP de prueba (sin eventos de startup: las migraciones ya se aplicaron)."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.fixture
def ip_headers():
    """Header con una IP única por test, para que el rate limiting no se mezcle entre tests."""
    return {"X-Forwarded-For": f"10.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}"}


@pytest.fixture
def business():
    """Crea un negocio con sucursal, profesional y servicio de 30 minutos."""
    conn = psycopg2.connect(TEST_DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password_hash, role, full_name) "
        "VALUES ('owner@example.com', 'x', 'owner', 'Owner Test') RETURNING id"
    )
    owner_id = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO businesses (owner_id, name, slug, min_advance_hours, plan_status) "
        "VALUES (%s, 'Test Clinic', 'test-clinic', 1, 'active') RETURNING id",
        (owner_id,),
    )
    business_id = cur.fetchone()[0]
    cur.execute("INSERT INTO branches (business_id, name) VALUES (%s, 'Main') RETURNING id", (business_id,))
    branch_id = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO professionals (business_id, branch_id, display_name) VALUES (%s, %s, 'Dr. Test') RETURNING id",
        (business_id, branch_id),
    )
    professional_id = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO services (business_id, name, duration_minutes) VALUES (%s, 'Consulta', 30) RETURNING id",
        (business_id,),
    )
    service_id = cur.fetchone()[0]
    conn.close()
    return {
        "slug": "test-clinic",
        "professional_id": str(professional_id),
        "service_id": str(service_id),
        "branch_id": str(branch_id),
    }


def slot(days_ahead: int = 3, hour: int = 10, minute: int = 0, minutes: int = 30) -> tuple[str, str]:
    """Devuelve (starts_at, ends_at) ISO en hora de Argentina, en el futuro."""
    start = (datetime.now(TZ_AR) + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return start.isoformat(), (start + timedelta(minutes=minutes)).isoformat()
