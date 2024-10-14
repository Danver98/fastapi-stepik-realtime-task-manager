import datetime

from sqlalchemy import BigInteger, SmallInteger, DateTime, func, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.api.schemas.user import Role


class User(Base):  # обязательно наследуем все модели от нашей Base-метатаблицы
    __tablename__ = "users"  # Указываем как будет называться наша таблица в базе данных (пишется в ед. числе)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)  # Строка  говорит, что наша колонка будет интом, но уточняет, что ещё и большим интом (актуально для ТГ-ботов), первичным ключом и индексироваться
    login: Mapped[str]  = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str]  = mapped_column(String, nullable=True)
    surname: Mapped[str] = mapped_column(String, nullable=True)
    password: Mapped[str] = mapped_column(String, nullable=True)
    roles: Mapped[tuple[Role]] = mapped_column(ARRAY(SmallInteger), nullable=True)
    logged: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    tokens: Mapped[list['TokenData'] | None] = relationship("TokenData", back_populates="user")
    tasks: Mapped[list['Task'] | None] = relationship("Task", back_populates="user")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user: Mapped[User | None] = relationship("User", back_populates="tasks")
    completed: Mapped[bool] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True, default=func.now())


class TokenData(Base):
    __tablename__ = "tokenData"
    __table_args__ = (
        UniqueConstraint("user_id", "fingerprint"),
    )
    id: Mapped[int | None] = mapped_column(BigInteger, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user: Mapped[User | None] = relationship("User", back_populates="tokens")
    refresh_token_uuid: Mapped[UUID] = mapped_column(UUID, nullable=True, unique=True)
    refresh_token: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    fingerprint: Mapped[str] = mapped_column(String, nullable=False, unique=False)
    expires_in: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

