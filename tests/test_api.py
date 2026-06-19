from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

client = TestClient(app)

@patch("app.api.process_booking.delay")
def test_create_booking(mock_celery):
    response = client.post("/bookings", json={
        "name": "John Doe",
        "datetime": "2026-06-20T10:00:00",
        "service_type": "consultation"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    mock_celery.assert_called_once()

def test_get_and_list_bookings():
    client.post("/bookings", json={
        "name": "Jane",
        "datetime": "2026-06-21T10:00:00",
        "service_type": "therapy"
    })
    assert client.get("/bookings").status_code == 200

def test_delete_booking():
    res = client.post("/bookings", json={
        "name": "Bob",
        "datetime": "2026-06-22T10:00:00",
        "service_type": "checkup"
    })
    booking_id = res.json()["id"]
    assert client.delete(f"/bookings/{booking_id}").status_code == 204
    assert client.get(f"/bookings/{booking_id}").status_code == 404
