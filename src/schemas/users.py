from pydantic import Field, EmailStr

from .base import CustomBase


class UserCreate(CustomBase):
    username: str = Field(..., examples=["ugo"])
    email: EmailStr
    password: str


class UserLogin(CustomBase):
    username: str = Field(..., examples=["ugo"])
    password: str


class UserJWT(CustomBase):
    access_token: str
