import os
import random
import logging
import json
# (пустая строка)
from celery import Celery
from sqlalchemy.orm import Session
import app.database
from app.models import Booking, BookingStatus
from dotenv import load_dotenv
import asyncio

# Windows compatibility for asyncio event loop
if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy') and hasattr(asyncio, 'set_event_loop_policy'):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Configure Celery with Windows compatibility
celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    broker_connection_retry_on_startup=True
)

# Ensure Windows event loop policy is set
import sys
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

@celery_app.task(bind=True, name="process_booking", max_retries=3, default_retry_delay=60)
def process_booking(self, booking_id: int):
    # Structured logging setup with custom JSON formatter
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": %(message)s}'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    # Create a fresh session for this task
    db = app.database.SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            logger.warning(json.dumps({"event": "booking_not_found", "booking_id": booking_id}))
            return

        # Проверка идемпотентности
        if booking.status != BookingStatus.PENDING:
            logger.info(json.dumps({"event": "booking_already_processed", "booking_id": booking_id, "status": booking.status}))
            return

        # Имитация сбоя с вероятностью 15%
        if random.random() < 0.15:
            booking.status = BookingStatus.FAILED
            db.commit()
            logger.info(json.dumps({"event": "booking_failed", "booking_id": booking_id, "reason": "random_failure"}))
            return

        booking.status = BookingStatus.CONFIRMED
        db.commit()
        logger.info(json.dumps({"event": "booking_confirmed", "booking_id": booking_id, "mock_notification_sent": True}))
    except Exception as e:
        logger.error(json.dumps({"event": "booking_processing_error", "booking_id": booking_id, "error": str(e)}))
        db.rollback()
        # Retry with exponential backoff
        try:
            self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.critical(json.dumps({"event": "booking_retries_exceeded", "booking_id": booking_id}))
    finally:
        db.close()
