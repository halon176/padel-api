from sqlalchemy import insert
from sqlalchemy.orm import Session

from src.controllers.models import reservation_relation


async def create_reservation_relation(
    user_id: int, reservation_id: int, session: Session
) -> reservation_relation:
    stmt = insert(reservation_relation).values(user_id=user_id, reservation_id=reservation_id)
    rr = session.execute(stmt)
    session.commit()
    return rr
