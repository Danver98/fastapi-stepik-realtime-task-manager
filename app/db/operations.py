from sqlalchemy import select, update, func, delete
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


async def get_refresh_token(session: AsyncSession, login: str, fingerprint: str) -> models.TokenData:
    """Get refresh token"""
    subquery = select(func.max(models.User.id)).where(models.User.login == login)
    query = select(models.TokenData).where(models.TokenData.user_id == subquery.scalar_subquery(),
                                           models.TokenData.fingerprint == fingerprint)
    result = await session.scalars(query)
    return result.first()


async def update_refresh_token(session: AsyncSession, old_refresh_token: models.TokenData, new_refresh_token: models.TokenData):
    """Create/update refresh token"""
    if old_refresh_token:
        await session.execute(delete(models.TokenData).where(models.TokenData.id == old_refresh_token.id))
    session.add(new_refresh_token)
    await session.commit()


async def delete_refresh_token(session: AsyncSession, login: str, fingerprint: str):
    """Create/update refresh token"""
    subquery = select(func.max(models.User.id)).where(models.User.login == login)
    statement = delete(models.TokenData).where(models.TokenData.user_id == subquery.scalar_subquery(),
                                               models.TokenData.fingerprint == fingerprint)
    await session.execute(statement)
    await session.commit()
