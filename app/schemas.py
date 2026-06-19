from pydantic import BaseModel
from datetime import datetime

class BookingBase(BaseModel):
    name: str
    datetime: datetime
    service_type: str

class BookingCreate(BookingBase):
    pass

class BookingResponse(BookingBase):
    id: int
    status: str

    class Config:
        from_attributes = True
