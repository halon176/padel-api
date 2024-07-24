from fastapi import APIRouter, HTTPException

from src.controllers.db import session_type
from src.controllers.users import get_user_by_username, create_user
from src.schemas.users import UserCreate, UserLogin, UserJWT
from src.security import sign_jwt

router = APIRouter(prefix="/users")


@router.post("", response_model=UserJWT, status_code=201)
async def create_user_ep(payload: UserCreate, session: session_type):
    user = await create_user(payload.username, payload.email, payload.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="Error creating user")
    return sign_jwt(user.id)


@router.post("/login", response_model=UserJWT)
async def user_login(payload: UserLogin, session: session_type):
    # get user obj from db
    user = await get_user_by_username(payload.username, session)

    # raise exception if user not found or password is wrong
    if not user or not user.check_password(payload.password):
        raise HTTPException(status_code=401, detail="Wrong user or password")

    # response with jwt token
    return sign_jwt(user.id)
