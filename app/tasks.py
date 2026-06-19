import os
import random
import logging
from celery import Celery
from sqlalchemy.orm import Session
import app.database
from app.models import Booking, BookingStatus
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

@celery_app.task(bind=True, name="process_booking")
def process_booking(self, booking_id: int):
    db: Session = app.database.SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            logging.warning(f"Booking {booking_id} not found.")
            return
        
        # Проверка идемпотентности
        if booking.status != BookingStatus.PENDING:
            logging.info(f"Booking {booking_id} already processed. Status: {booking.status}")
            return

        # Имитация сбоя с вероятностью 15%
        if random.random() < 0.15:
            booking.status = BookingStatus.FAILED
            db.commit()
            logging.info(f"Booking {booking_id} failed.")
            return

        booking.status = BookingStatus.CONFIRMED
        db.commit()
        logging.info(f"Booking {booking_id} confirmed. Mock notification sent.")
    except Exception as e:
        logging.error(f"Error processing booking {booking_id}: {e}")
        db.rollback()
    finally:
        db.close()
