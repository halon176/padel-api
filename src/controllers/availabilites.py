from datetime import datetime

from sqlalchemy.orm import Session

from src.controllers.models import Availability


async def create_availability(
    user_id: int, start: datetime, end: datetime, session: Session
) -> Availability:
    a = Availability(user_id=user_id, start=start, end=end)
    session.add(a)
    session.commit()
    return a


async def get_availability(start: datetime, end: datetime, session: Session) -> list[Availability]:
    a = (
        session.query(Availability)
        .filter(Availability.start == start, Availability.end == end)
        .all()
    )
    return a


async def get_user_availability(user_id: int, session: Session) -> list[Availability]:
    a = session.query(Availability).filter(Availability.user_id == user_id).all()
    return a
