from datetime import datetime

from sqlalchemy.orm import Session

from src.controllers.models import Reservation


async def get_reservation(start: datetime, end: datetime, session: Session) -> Reservation:
    r = (
        session.query(Reservation)
        .filter(Reservation.start == start, Reservation.end == end)
        .first()
    )
    return r


async def get_all_reservations(session: Session) -> list[Reservation]:
    return session.query(Reservation).all()


async def create_reservation(start: datetime, end: datetime, session: Session) -> Reservation:
    r = Reservation(start=start, end=end)
    session.add(r)
    session.commit()
    return r


async def get_all_user_reservations(user_id: int, session: Session) -> list[Reservation]:
    return (
        session.query(Reservation)
        .join(Reservation.users)
        .filter(Reservation.users.any(id=user_id))
        .all()
    )
