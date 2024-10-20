import json
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.api.schemas.user import UserRegister
from app.db import operations
from app.core.security import (hash_password, verify_password, create_access_token, create_fingerprint,
                               REFRESH_TOKEN_EXPIRATION_TIME, create_refresh_token_uuid, REDIS_USERS_TOKEN_DATA_KEY,
                               MAX_CONCURRENT_USER_SESSIONS)
from app.core.config import settings
# class AuthService(metaclass=Singleton):
# We should create new service instance for each request (ain't good solution IMHO)
class AuthService():
    """
        Service class for working with users
    """
    def __init__(self, session: AsyncSession = None, redis_session: Redis = None):
        self._session = session
        self._redis = redis_session

    async def set_user_session(self, login: str, user_id: int, fingerprint: str, refresh_token: str,
                               check_session_count=False):
        """Set user session"""
        # Check if user already has sessions. Limit number is 5
        hash_name = REDIS_USERS_TOKEN_DATA_KEY + ':' + login
        if check_session_count and await self._redis.hlen(hash_name) >= MAX_CONCURRENT_USER_SESSIONS:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login sessions")

        created_at = datetime.now(timezone.utc)
        user_session_data = {
            'user_id': user_id,
            'refresh_token': refresh_token,
            'expires_in': REFRESH_TOKEN_EXPIRATION_TIME.total_seconds(),
            'created_at': created_at
        }
        await self._redis.hset(hash_name, fingerprint, json.dumps(user_session_data, default=str))

    async def validate_refresh_token(self, login: str, fingerprint: str, raw_refresh_token: str) -> str:
        """Validate refresh token from Redis"""
        hash_name = REDIS_USERS_TOKEN_DATA_KEY + ':' + login
        user_session_data = await self._redis.hget(hash_name, fingerprint)
        if not user_session_data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found")

        user_session_data = json.loads(user_session_data)
        # Cyphered token
        refresh_token = user_session_data.get('refresh_token')
        if not verify_password(raw_refresh_token, refresh_token, salt=settings.REFRESH_TOKEN_PASSWORD_SALT):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token mismatch")

        expires_in = user_session_data.get('expires_in')
        created_at = datetime.strptime(user_session_data.get('created_at'), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=timezone.utc)
        if (datetime.now(timezone.utc) - created_at).total_seconds() > expires_in:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        return refresh_token

    async def delete_session(self, login: str, fingerprint: str):
        """Delete user session"""
        hash_name = REDIS_USERS_TOKEN_DATA_KEY + ':' + login
        await self._redis.hdel(hash_name, fingerprint)

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
        refresh_token, hashed_refresh_token = create_refresh_token_uuid()
        await self.set_user_session(data.username, db_user.id, fingerprint, hashed_refresh_token, check_session_count=True)
        return (access_token, refresh_token, fingerprint)

    async def logout(self, login: str, fingerprint: str):
        """Logout user method"""
        await operations.logout_user(self._session, login)
        # Delete refresh_token associated with user and fingerprint
        await self.delete_session(login, fingerprint)

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
        await self.validate_refresh_token(login, fingerprint, current_refresh_token)

        refresh_token, hashed_refresh_token = create_refresh_token_uuid()
        await self.set_user_session(login, db_user.id, fingerprint, hashed_refresh_token)
        return (access_token, refresh_token, fingerprint)
