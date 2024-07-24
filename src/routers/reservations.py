from fastapi import APIRouter, Depends

from src.controllers.db import session_type
from src.controllers.reservations import get_all_reservations, get_all_user_reservations
from src.schemas.reservations import ReservationResponse
from src.security import JWTBearer

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("/", name="List of all reservations", response_model=list[ReservationResponse])
async def get_all_reservations_ep(session: session_type):
    return await get_all_reservations(session)


@router.get("/me", name="List of my reservations", response_model=list[ReservationResponse])
async def get_my_reservations(session: session_type, user_id: int = Depends(JWTBearer())):
    return await get_all_user_reservations(user_id, session)
