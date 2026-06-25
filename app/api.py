from fastapi import APIRouter, Depends, HTTPException, Query
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Booking, BookingStatus
from app.schemas import BookingCreate, BookingResponse
from app.tasks import process_booking

from fastapi import Request
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/bookings", response_model=BookingResponse, status_code=201)
@limiter.limit("5/minute")
def create_booking(request: Request, booking: BookingCreate, db: Session = Depends(get_db)):
    db_booking = Booking(**booking.model_dump(), status=BookingStatus.PENDING)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    # Запуск фоновой задачи
    process_booking.delay(db_booking.id)
    return db_booking

@router.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@router.get("/bookings", response_model=List[BookingResponse])
def list_bookings(
    status: Optional[str] = Query(None, description="Filter: pending, confirmed, failed"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Booking)
    if status:
        if status not in [e.value for e in BookingStatus]:
            raise HTTPException(status_code=400, detail="Invalid status filter")
        query = query.filter(Booking.status == status)
    return query.offset(skip).limit(limit).all()

@router.delete("/bookings/{booking_id}", status_code=204)
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only cancel pending bookings")
    
    db.delete(booking)
    db.commit()
    return None
