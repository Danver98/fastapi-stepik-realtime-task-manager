import datetime

from sqlalchemy import BigInteger, SmallInteger, DateTime, func, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.api.schemas.user import Role


class User(Base):
    """User model"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    login: Mapped[str]  = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str]  = mapped_column(String, nullable=True)
    surname: Mapped[str] = mapped_column(String, nullable=True)
    password: Mapped[str] = mapped_column(String, nullable=True)
    roles: Mapped[tuple[Role]] = mapped_column(ARRAY(SmallInteger), nullable=True)
    logged: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    tasks: Mapped[list['Task'] | None] = relationship("Task", back_populates="user")


class Task(Base):
    """Task model"""
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user: Mapped[User | None] = relationship("User", back_populates="tasks")
    completed: Mapped[bool] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True, default=func.now())
