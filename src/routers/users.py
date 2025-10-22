from fastapi import APIRouter, HTTPException, Request

from src.controllers.db import session_type
from src.controllers.users import get_user_by_username, create_user
from src.rate_limiter import limiter
from src.schemas.users import UserCreate, UserLogin, UserJWT
from src.security import sign_jwt

router = APIRouter(prefix="/users")


@router.post("", response_model=UserJWT, status_code=201)
@limiter.limit("5/minute")  # Max 5 registrations per minute per IP
async def create_user_ep(request: Request, payload: UserCreate, session: session_type):
    user = await create_user(payload.username, payload.email, payload.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="Error creating user")
    return sign_jwt(user.id)


@router.post("/login", response_model=UserJWT)
@limiter.limit("10/minute")  # Max 10 login attempts per minute per IP (brute force protection)
async def user_login(request: Request, payload: UserLogin, session: session_type):
    # get user obj from db
    user = await get_user_by_username(payload.username, session)

    # raise exception if user not found or password is wrong
    if not user or not user.check_password(payload.password):
        raise HTTPException(status_code=401, detail="Wrong user or password")

    # response with jwt token
    return sign_jwt(user.id)
