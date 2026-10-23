import os
import uuid

import pytest

from clients.booker_client import BookerClient

MARKER = "qa-suite"


@pytest.fixture(scope="session")
def client():
    """Provides a shared API client and close its session after all tests."""
    api_client = BookerClient()
    yield api_client
    api_client.close()


@pytest.fixture
def auth(client):
    """Get a valid authentication token for protected API operations: PUT, PATCH, DELETE"""
    username = os.environ["API_USERNAME"]
    password = os.environ["API_PASSWORD"]

    response = client.create_token(username, password)

    assert response.status_code == 200

    token = response.json().get("token")
    assert isinstance(token, str) and token

    return {"cookies": {"token": token}}


@pytest.fixture
def payload():
    """Booking data with a unique ownership marker."""
    return {
        "firstname": f"qa-{uuid.uuid4().hex[:8]}",
        "lastname": MARKER,
        "totalprice": 150,
        "depositpaid": True,
        "bookingdates": {"checkin": "2026-11-03", "checkout": "2026-11-07"},
        "additionalneeds": f"qa-{uuid.uuid4().hex}",
    }


@pytest.fixture
def booking_cleanup(client, auth):
    """Track bookings created during a test and clean them up afterward."""
    created_bookings = []

    yield created_bookings

    for booking_id, marker in created_bookings:
        stored = client.get_booking_by_id(booking_id)

        # Delete only if the booking still exists and is still ours.
        if stored.status_code == 200 and stored.json().get("additionalneeds") == marker:
            client.delete_booking(booking_id, **auth)


@pytest.fixture
def booking_id(client, payload, booking_cleanup):
    """A booking created for a test, deleted afterwards."""
    response = client.create_booking(payload)
    assert response.status_code == 200, (
        f"SETUP failed: POST /booking -> {response.status_code}: {response.text}"
    )
    booking_id = response.json()["bookingid"]
    booking_cleanup.append((booking_id, payload["additionalneeds"]))

    return booking_id


@pytest.fixture(autouse=True)
def no_leftover_cookies(client):
    """Clear cookies before each test to prevent authentication leakage."""
    client.session.cookies.clear()
