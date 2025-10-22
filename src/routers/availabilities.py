import logging
from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from src.controllers.availabilites import (
    create_availability,
    get_availability,
    get_user_availability,
)
from src.controllers.db import session_type
from src.controllers.reservation_relations import create_reservation_relation
from src.controllers.reservations import create_reservation, get_reservation
from src.controllers.users import get_users_by_ids
from src.schemas.availabilities import AvailabilityCreate, AvailabilityResponse
from src.security import JWTBearer
from src.utils.notifications import send_notification

router = APIRouter(prefix="/availabilities", tags=["availabilities"])


@router.post("", name="Create availability", status_code=201, response_model=AvailabilityResponse)
async def create_availability_ep(
    payload: AvailabilityCreate,
    session: session_type,
    bg_tasks: BackgroundTasks,
    user_id: int = Depends(JWTBearer()),
):
    start_datetime = datetime.combine(payload.date, time(payload.slot_start_hour))
    end_datetime = start_datetime + timedelta(hours=1)

    # RACE CONDITION FIX: Use transaction with SELECT FOR UPDATE lock
    try:
        # check if a reservation for the same slot exists
        reservation_exists = await get_reservation(start_datetime, end_datetime, session)
        if reservation_exists:
            raise HTTPException(status_code=400, detail="Slot is busy")

        # Use lock=True to prevent race conditions when checking/creating availabilities
        a_exists = await get_availability(start_datetime, end_datetime, session, lock=True)
        exists_user_ids = [a.user_id for a in a_exists]

        if user_id in exists_user_ids:
            raise HTTPException(status_code=400, detail="Slot is already booked")

        # Create availability without auto-commit (part of transaction)
        a = await create_availability(user_id, start_datetime, end_datetime, session, auto_commit=False)
        exists_user_ids.append(user_id)
        a_exists.append(a)

        # if 4 users are available, create reservation
        if len(a_exists) >= 4:
            reservation = await create_reservation(start_datetime, end_datetime, session)
            for a_item in a_exists:
                await create_reservation_relation(a_item.user_id, reservation.id, session)

            # send notification to users
            users = await get_users_by_ids(exists_user_ids, session)
            # use background task to send notification to make the response faster
            bg_tasks.add_task(send_notification, users, start_datetime, end_datetime)

        # Commit the entire transaction atomically
        session.commit()

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        logging.error(f"sql error: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail="Error creating availability/reservation")

    return a


@router.get("", name="Get my availabilities", response_model=list[AvailabilityResponse])
async def get_my_availabilities(session: session_type, user_id: int = Depends(JWTBearer())):
    return await get_user_availability(user_id, session)
