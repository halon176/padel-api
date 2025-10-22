from datetime import datetime

from sqlalchemy.orm import Session

from src.controllers.models import Availability


async def create_availability(
    user_id: int, start: datetime, end: datetime, session: Session, auto_commit: bool = True
) -> Availability:
    a = Availability(user_id=user_id, start=start, end=end)
    session.add(a)
    if auto_commit:
        session.commit()
    else:
        session.flush()  # Get the ID without committing
    return a


async def get_availability(
    start: datetime, end: datetime, session: Session, lock: bool = False
) -> list[Availability]:
    query = session.query(Availability).filter(
        Availability.start == start, Availability.end == end
    )
    # Use SELECT FOR UPDATE to prevent race conditions when creating reservations
    if lock:
        query = query.with_for_update()
    return query.all()


async def get_user_availability(user_id: int, session: Session) -> list[Availability]:
    a = session.query(Availability).filter(Availability.user_id == user_id).all()
    return a
