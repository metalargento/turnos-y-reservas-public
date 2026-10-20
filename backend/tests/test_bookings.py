"""Tests del flujo público de reservas: crear, evitar doble reserva y cancelar."""
from tests.conftest import slot

CLIENT = {"client_name": "Maria Perez", "client_email": "maria@example.com", "client_phone": "1155550000"}


def book(client, business, starts_at, ends_at, **overrides):
    """Hace POST de una reserva pública con los datos del negocio de prueba."""
    payload = {
        "professional_id": business["professional_id"],
        "service_id": business["service_id"],
        "branch_id": business["branch_id"],
        "starts_at": starts_at,
        "ends_at": ends_at,
        **CLIENT,
        **overrides,
    }
    return client.post(f"/public/bookings/{business['slug']}", json=payload)


def test_create_booking(client, business):
    starts, ends = slot()
    response = book(client, business, starts, ends)

    assert response.status_code == 201
    booking = response.json()["booking"]
    assert booking["status"] == "confirmed"
    assert booking["confirmation_token"]


def test_same_slot_cannot_be_booked_twice(client, business):
    starts, ends = slot()
    assert book(client, business, starts, ends).status_code == 201

    second = book(client, business, starts, ends, client_email="otra@example.com")

    assert second.status_code == 409


def test_overlapping_slot_is_rejected_but_adjacent_slot_is_allowed(client, business):
    first = slot(hour=10, minute=0)
    assert book(client, business, *first).status_code == 201

    overlapping = slot(hour=10, minute=15)
    assert book(client, business, *overlapping).status_code == 409

    adjacent = slot(hour=10, minute=30)
    assert book(client, business, *adjacent).status_code == 201


def test_booking_in_the_past_is_rejected(client, business):
    starts, ends = slot(days_ahead=-1)
    assert book(client, business, starts, ends).status_code == 400


def test_booking_unknown_business_returns_404(client, business):
    starts, ends = slot()
    response = client.post("/public/bookings/does-not-exist", json={
        "professional_id": business["professional_id"],
        "service_id": business["service_id"],
        "starts_at": starts,
        "ends_at": ends,
        **CLIENT,
    })
    assert response.status_code == 404


def test_cancel_with_email_and_name_frees_the_slot(client, business):
    starts, ends = slot()
    booking = book(client, business, starts, ends).json()["booking"]

    cancel = client.post(
        f"/public/bookings/{business['slug']}/cancel",
        params={"booking_id": booking["id"], "client_email": CLIENT["client_email"], "client_name": CLIENT["client_name"]},
    )
    assert cancel.status_code == 200
    assert cancel.json()["booking"]["status"] == "cancelled"

    assert book(client, business, starts, ends, client_email="nuevo@example.com").status_code == 201


def test_cancel_with_wrong_name_is_rejected(client, business):
    starts, ends = slot()
    booking = book(client, business, starts, ends).json()["booking"]

    cancel = client.post(
        f"/public/bookings/{business['slug']}/cancel",
        params={"booking_id": booking["id"], "client_email": CLIENT["client_email"], "client_name": "Someone Else"},
    )
    assert cancel.status_code == 401


def test_cancel_with_confirmation_token(client, business):
    starts, ends = slot()
    token = book(client, business, starts, ends).json()["booking"]["confirmation_token"]

    cancel = client.post(
        f"/public/bookings/confirm/{token}/cancel",
        json={"cancellation_reason": "No puedo asistir"},
    )
    assert cancel.status_code == 200
    assert cancel.json()["booking"]["status"] == "cancelled"

    again = client.post(f"/public/bookings/confirm/{token}/cancel", json={})
    assert again.status_code in (400, 409)


def test_minimum_advance_hours_is_enforced(client, business):
    """El negocio de prueba exige 1 hora de anticipación: una reserva en 30 minutos se rechaza."""
    from datetime import datetime, timedelta
    from tests.conftest import TZ_AR

    start = datetime.now(TZ_AR) + timedelta(minutes=30)
    response = book(client, business, start.isoformat(), (start + timedelta(minutes=30)).isoformat())

    assert response.status_code == 400


def test_database_rejects_overlapping_bookings_even_if_validation_is_skipped(client, business, monkeypatch):
    """Simula una condición de carrera: sin la validación previa, la base debe impedir la superposición."""
    from repositories.booking_repo import booking_repo
    starts, ends = slot()
    assert book(client, business, starts, ends).status_code == 201

    monkeypatch.setattr(booking_repo, "find_conflicts", lambda *args, **kwargs: [])
    second = book(client, business, starts, ends, client_email="otra@example.com")

    assert second.status_code == 409


def test_cancelled_booking_does_not_block_the_database_constraint(client, business):
    """La restricción solo aplica a reservas activas: tras cancelar se puede volver a reservar."""
    starts, ends = slot()
    booking = book(client, business, starts, ends).json()["booking"]
    client.post(
        f"/public/bookings/{business['slug']}/cancel",
        params={"booking_id": booking["id"], "client_email": CLIENT["client_email"], "client_name": CLIENT["client_name"]},
    )

    assert book(client, business, starts, ends, client_email="otra@example.com").status_code == 201
