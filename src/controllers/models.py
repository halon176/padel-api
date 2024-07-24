from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy import (
    Integer,
    Text,
    Boolean,
    func,
    DateTime,
    Table,
    ForeignKey,
    Column,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.controllers.db import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

reservation_relation = Table(
    "reservation_relations",
    Base.metadata,
    Column(
        "user_id", ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "reservation_id",
        ForeignKey("reservations.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, unique=True)
    email: Mapped[str] = mapped_column(Text, unique=True)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    availabilities: Mapped[list["Availability"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation",
        secondary=reservation_relation,
        back_populates="users",
    )

    @property
    def password_setter(self):
        raise AttributeError("Password can't be read")

    @password_setter.setter
    def password_setter(self, password: str) -> None:
        self.password = pwd_context.hash(password)

    def check_password(self, plane_password: str) -> bool:
        return pwd_context.verify(plane_password, self.password)


class Availability(Base):
    __tablename__ = "availabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    start: Mapped[datetime]
    end: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="availabilities")

    __table_args__ = (UniqueConstraint("user_id", "start", "end", name="uix_1"),)


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start: Mapped[datetime]
    end: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=reservation_relation,
        back_populates="reservations",
    )

    __table_args__ = (UniqueConstraint("start", "end", name="uix_2"),)
