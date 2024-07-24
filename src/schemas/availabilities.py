from datetime import datetime

from pydantic import Field, FutureDate

from .base import CustomBase


class AvailabilityCreate(CustomBase):
    date: FutureDate = Field(..., description="Date must be in the future, next day or later")
    slot_start_hour: int = Field(..., ge=9, le=22, examples=[10])


class AvailabilityResponse(CustomBase):
    start: datetime
    end: datetime
    created_at: datetime
