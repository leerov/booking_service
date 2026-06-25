import pytest
from unittest.mock import patch
from datetime import datetime
from app.tasks import process_booking
from app.models import Booking, BookingStatus
import app.database

def test_worker_success():
    # Create a clean session for this test
    db = app.database.SessionLocal()
    booking = Booking(name="Test", datetime=datetime(2026, 6, 20, 10, 0, 0), service_type="test", status=BookingStatus.PENDING)
    db.add(booking)
    db.commit()
    booking_id = booking.id
    db.close()

    # Use a fresh session for the worker test
    with patch("random.random", return_value=0.5): # > 0.15
        process_booking(booking_id)

    # Verify with a fresh session
    db = app.database.SessionLocal()
    result = db.query(Booking).filter(Booking.id == booking_id).first()
    assert result is not None
    assert result.status == BookingStatus.CONFIRMED
    db.close()

def test_worker_failure():
    # Create a clean session for this test
    db = app.database.SessionLocal()
    booking = Booking(name="Test", datetime=datetime(2026, 6, 20, 10, 0, 0), service_type="test", status=BookingStatus.PENDING)
    db.add(booking)
    db.commit()
    booking_id = booking.id
    db.close()

    # Use a fresh session for the worker test
    with patch("random.random", return_value=0.05): # < 0.15
        process_booking(booking_id)

    # Verify with a fresh session
    db = app.database.SessionLocal()
    result = db.query(Booking).filter(Booking.id == booking_id).first()
    assert result is not None
    assert result.status == BookingStatus.FAILED
    db.close()
