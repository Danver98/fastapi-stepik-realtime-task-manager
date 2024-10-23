from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import UniqueViolationError
from app.api.endpoints.users import UserRegister
from app.db import models
from app.api.endpoints.errors.models import UserRegistrationError


async def create_user(session: AsyncSession, user: UserRegister) -> models.User:
    """Create db user"""
    db_user = models.User(**user.model_dump())
    session.add(db_user)
    try:
        await session.commit()
        await session.refresh(db_user)
    except (UniqueViolationError, IntegrityError) as ex:
        raise UserRegistrationError(str(ex)) from ex
    return db_user


async def get_user(session: AsyncSession, id_: int) -> models.User:
    """Get db user by id"""
    result = await session.execute(select(models.User).where(models.User.id == id_).limit(1))
    return result.scalar_one()


async def get_user_by_login(session: AsyncSession, login: str) -> models.User:
    """Get db user by login"""
    result = await session.execute(select(models.User).where(models.User.login == login).limit(1))
    return result.scalar_one()


async def login_user(session: AsyncSession, login: str, db_user: models.User = None) -> models.User:
    """login user in db"""
    statement = update(models.User).where(models.User.login == login).values(
        {
            'logged': True
        }
    )
    await session.execute(statement)
    await session.commit()
    if db_user:
        await session.refresh(db_user)
    return


async def logout_user(session: AsyncSession, login: str) -> models.User:
    """logout user from db"""
    statement = update(models.User).where(models.User.login == login).values(
        {
            'logged': False
        }
    )
    await session.execute(statement)
    await session.commit()
    return
