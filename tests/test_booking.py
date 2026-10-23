import os

import pytest


# ---------- Booking lifecycle ----------
def test_create_booking(client, payload, booking_cleanup):
    # Given: valid booking data

    # When: a booking is created
    response = client.create_booking(payload)

    # Then: the booking is created with an ID and the submitted data
    assert response.status_code == 200, response.text
    data = response.json()
    booking_cleanup.append((data["bookingid"], payload["additionalneeds"]))

    assert isinstance(data["bookingid"], int)
    assert data["booking"] == payload


def test_get_booking_by_id(client, booking_id, payload):
    # Given: an existing booking

    # When: the booking is retrieved by ID
    response = client.get_booking_by_id(booking_id)

    # Then: the stored booking matches the submitted data
    assert response.status_code == 200, response.text
    assert response.json() == payload


def test_get_booking_ids_by_name(client, booking_id, payload):
    # Given: an existing booking with a unique first name

    # When: booking IDs are filtered by first and last name
    response = client.get_booking_ids(
        firstname=payload["firstname"], lastname=payload["lastname"]
    )

    # Then: the created booking is in the results
    assert response.status_code == 200, response.text
    booking_ids = [item["bookingid"] for item in response.json()]
    assert booking_id in booking_ids


def test_update_booking_put(client, booking_id, payload, auth):
    # Given: an existing booking and new data for all fields
    updated = {**payload, "firstname": "Anna", "lastname": "Brown", "totalprice": 250}

    # When: the booking is fully updated with PUT
    response = client.replace_booking(booking_id, updated, **auth)

    # Then: the response contains the updated data
    assert response.status_code == 200, response.text
    assert response.json() == updated

    # And: the changes are saved
    stored = client.get_booking_by_id(booking_id)
    assert stored.status_code == 200, "Booking disappeared (shared instance reset?)"
    assert stored.json() == updated


def test_partial_update_booking(client, booking_id, payload, auth):
    # Given: an existing booking and a change to one field
    change = {"firstname": "Anna"}
    expected = {**payload, **change}

    # When: the booking is partially updated with PATCH
    response = client.update_booking(booking_id, change, **auth)

    # Then: only that field changed
    assert response.status_code == 200, response.text
    assert response.json() == expected

    # And: the changes are saved
    stored = client.get_booking_by_id(booking_id)
    assert stored.status_code == 200, "Booking disappeared (shared instance reset?)"
    assert stored.json() == expected


def test_delete_booking(client, booking_id, auth):
    # Given: an existing booking

    # When: the booking is deleted
    response = client.delete_booking(booking_id, **auth)

    # Then: the deletion succeeds (201 is the documented response)
    assert response.status_code == 201, response.text

    # And: the booking can no longer be found (404 is an assumption)
    assert client.get_booking_by_id(booking_id).status_code == 404


# ---------- Authentication ----------
def test_auth_with_valid_credentials(client):
    # Given: the documented demo credentials
    username = os.environ["API_USERNAME"]
    password = os.environ["API_PASSWORD"]

    # When: a token is requested
    response = client.create_token(username, password)

    # Then: a non-empty token is returned
    assert response.status_code == 200, response.text
    assert response.json().get("token")


@pytest.mark.parametrize(
    "username, password",
    [
        pytest.param("wrong-user", "password123", id="wrong-username"),
        pytest.param("admin", "wrong-password", id="wrong-password"),
        pytest.param("", "", id="empty-credentials"),
    ],
)
def test_invalid_authentication(client, username, password):
    # Given: invalid credentials

    # When: a token is requested
    response = client.create_token(username, password)

    # Then: no token is returned (current behavior: 200 + "reason", not documented)
    assert response.status_code == 200
    assert "token" not in response.json()
    assert "reason" in response.json()


# ---------- Input validation and negative cases ----------
@pytest.mark.parametrize(
    "booking_id", [999999999, -1], ids=["nonexistent-id", "negative-id"]
)
def test_get_nonexistent_booking(client, booking_id):
    # Given: a booking ID that does not exist

    # When: the booking is retrieved
    response = client.get_booking_by_id(booking_id)

    # Then: it is not found (404 is an assumption, not documented)
    assert response.status_code == 404, response.text


def test_create_booking_missing_field(client, payload):
    # Given: booking data without a required field
    del payload["firstname"]

    # When: a booking is created
    response = client.create_booking(payload)

    # Then: it is rejected (400 is a proposed requirement)
    assert response.status_code == 400, response.text


def test_create_booking_checkout_before_checkin(client, payload, booking_cleanup):
    # Given: booking data where checkout is before checkin
    payload["bookingdates"] = {"checkin": "2026-11-10", "checkout": "2026-11-05"}

    # When: a booking is created
    response = client.create_booking(payload)
    if response.status_code == 200:
        booking_cleanup.append(
            (response.json()["bookingid"], payload["additionalneeds"])
        )

    # Then: it is rejected (400 is a proposed requirement)
    assert response.status_code == 400, response.text
