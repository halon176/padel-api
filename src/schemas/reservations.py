from datetime import datetime

from .base import CustomBase


class ReservationResponse(CustomBase):
    start: datetime
    end: datetime
    created_at: datetime
