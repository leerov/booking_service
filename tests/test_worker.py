import pytest
from unittest.mock import patch
from app.tasks import process_booking
from app.models import Booking, BookingStatus
import app.database

def test_worker_success():
    db = app.database.SessionLocal()
    booking = Booking(name="Test", datetime="2026-06-20T10:00:00", service_type="test", status=BookingStatus.PENDING)
    db.add(booking)
    db.commit()
    booking_id = booking.id
    db.close()

    with patch("random.random", return_value=0.5): # > 0.15
        process_booking(booking_id)

    db = app.database.SessionLocal()
    assert db.query(Booking).filter(Booking.id == booking_id).first().status == BookingStatus.CONFIRMED
    db.close()

def test_worker_failure():
    db = app.database.SessionLocal()
    booking = Booking(name="Test", datetime="2026-06-20T10:00:00", service_type="test", status=BookingStatus.PENDING)
    db.add(booking)
    db.commit()
    booking_id = booking.id
    db.close()

    with patch("random.random", return_value=0.05): # < 0.15
        process_booking(booking_id)

    db = app.database.SessionLocal()
    assert db.query(Booking).filter(Booking.id == booking_id).first().status == BookingStatus.FAILED
    db.close()
