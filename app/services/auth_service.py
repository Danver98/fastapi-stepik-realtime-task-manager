from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.api.schemas.user import UserRegister
from app.db import operations, models
from app.core.security import (hash_password, verify_password, create_access_token, create_refresh_token, create_fingerprint,
                               REFRESH_TOKEN_EXPIRATION_TIME, create_refresh_token_uuid)
from app.core.config import settings
# class AuthService(metaclass=Singleton):
# We should create new service instance for each request (ain't good solution IMHO)
class AuthService():
    """
        Service class for working with users
    """
    def __init__(self, session: AsyncSession):
        self._session = session

    async def register(self, data: UserRegister):
        """Register user method"""
        data.password = hash_password(data.password)
        return await operations.create_user(self._session, data)

    async def get_user(self, id_: int):
        """Get user method"""
        return await operations.get_user(self._session, id_)

    async def login(self, data: OAuth2PasswordRequestForm, fingerprint: str = None) -> tuple[str, str, str]:
        """Login user method"""
        db_user = await operations.get_user_by_login(self._session, data.username)
        if db_user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")
        # if db_user.logged:
        #     raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User's already been authenticated")
        if not verify_password(data.password, db_user.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong Password")
        token_data = {
            'sub': db_user.login,
            'name': db_user.name,
            'surname': db_user.surname,
            'roles': db_user.roles
        }
        # login_user will commit changes what'll cause session's objects expiration and their attributes'll be loaded from db
        # again at next invokation to them. Can be circumvented by using Session.expire_on_commit=False
        await operations.login_user(self._session, db_user.login, db_user)
        access_token = create_access_token(token_data)
        fingerprint = fingerprint or create_fingerprint(data.username)
        created_at = datetime.now(timezone.utc)
        refresh_token, hashed_refresh_token = create_refresh_token_uuid()
        await operations.update_refresh_token(self._session, None, models.TokenData(
            user_id = db_user.id,
            fingerprint = fingerprint,
            refresh_token = hashed_refresh_token, #refresh_token
            expires_in = REFRESH_TOKEN_EXPIRATION_TIME.total_seconds() * 1000,
            created_at=created_at
        ))
        return (access_token, refresh_token, fingerprint)

    async def logout(self, login: str, fingerprint: str):
        """Logout user method"""
        await operations.logout_user(self._session, login)
        # Delete refresh_token associated with user and fingerprint
        await operations.delete_refresh_token(self._session, login, fingerprint)

    async def reissue_tokens(self, login: str, current_refresh_token: str, fingerprint: str) -> tuple[str, str, str]:
        """Reissue tokens method"""
        db_user = await operations.get_user_by_login(self._session, login)
        token_data = {
            'sub': db_user.login,
            'name': db_user.name,
            'surname': db_user.surname,
            'roles': db_user.roles
        }
        access_token = create_access_token(token_data)
        # TODO: cypher new_refresh_token before storing in DB
        current_refresh_token_obj: models.TokenData = await operations.get_refresh_token(self._session, login, fingerprint)
        if current_refresh_token_obj is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found")
        if current_refresh_token_obj.fingerprint != fingerprint:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Fingerprint mismatch")
        if not verify_password(current_refresh_token,
                           current_refresh_token_obj.refresh_token,
                           salt=settings.REFRESH_TOKEN_PASSWORD_SALT):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token mismatch")

        created_at = datetime.now(timezone.utc)
        refresh_token, hashed_refresh_token = create_refresh_token_uuid()
        token_data = models.TokenData(
            user_id = current_refresh_token_obj.user_id,
            fingerprint = fingerprint,
            refresh_token = hashed_refresh_token,
            expires_in = REFRESH_TOKEN_EXPIRATION_TIME.microseconds,
            created_at=created_at

        )
        # Delete current_refresh_token and insert new one
        await operations.update_refresh_token(self._session, current_refresh_token_obj, token_data)
        return (access_token, refresh_token, fingerprint)
