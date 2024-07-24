import logging

from sqlalchemy.orm import Session

from src.controllers.models import User


async def get_user_by_username(username: str, session: Session) -> User | None:
    user = session.query(User).filter(User.username == username, User.is_active == True).first()
    return user


async def get_users_by_ids(ids: list[int], session: Session) -> list[User]:
    return session.query(User).where(User.id.in_(ids)).all()


async def create_user(username: str, email: str, password: str, session: Session) -> User | None:
    user = User(username=username, email=email, password_setter=password)

    session.add(user)
    try:
        session.commit()
    except Exception as e:
        logging.error(e)
        session.rollback()
        return None
    return user
