from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from app.database import Base
import enum
from datetime import datetime

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    datetime = Column(DateTime, default=datetime.utcnow)
    service_type = Column(String)
    status = Column(SAEnum(BookingStatus), default=BookingStatus.PENDING)
