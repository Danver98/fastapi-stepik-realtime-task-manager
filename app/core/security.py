"""
    Contains functions for working with JWT and auth process
"""
import secrets
import uuid
from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
import jwt
from passlib.context import CryptContext
from app.api.schemas import user
from .config import settings


ALGORITHM = "HS256" # плюс в реальной жизни мы устанавливаем "время жизни" токена
EXPIRATION_TIME = timedelta(minutes=30)
REFRESH_TOKEN_EXPIRATION_TIME = timedelta(days=2)
REFRESH_TOKEN_HEADER = 'X-Refresh-Token'
FINGERPRINT_HEADER = 'X-Fingerprint'
REDIS_USERS_TOKEN_DATA_KEY = 'users_token_data'
MAX_CONCURRENT_USER_SESSIONS = 5
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
expiration_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token's expired. Try to obtain one more",
    headers={"WWW-Authenticate": "Bearer"},
)


def create_access_token(data: dict) -> str:
    """Creates access token"""
    data.update({
        'exp': datetime.now(timezone.utc) + EXPIRATION_TIME
    })
    return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> tuple[str, str]:
    """
        Creates refresh token and hashed version of it to store in database

        data: dict - data to encode in JWT token

        returns: tuple of refresh token itself and its hashed version
    """
    data.update({
        'exp': datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRATION_TIME
    })
    token = jwt.encode(data, settings.JWT_REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return token, hash_password(token, salt=settings.REFRESH_TOKEN_PASSWORD_SALT)

def create_refresh_token_uuid() -> tuple[uuid.UUID, str]:
    """
        Creates refresh token as UUID
    """
    token = uuid.uuid4()
    return token, hash_password(str(token), salt=settings.REFRESH_TOKEN_PASSWORD_SALT)


def decode_jwt_token(token: str, secret_key: str) -> dict:
    """Decodes JWT token"""
    try:
        return jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise expiration_exception
    except jwt.InvalidTokenError:
        raise credentials_exception


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """Returns info about current logged user"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return user.User(
            login=payload.get('sub'),
            name=payload.get('name'),
            surname=payload.get('surname'),
            roles=payload.get('roles')
        )
    except jwt.ExpiredSignatureError:
        raise expiration_exception
    except jwt.InvalidTokenError:
        raise credentials_exception


async def get_current_user_websocket(websocket: WebSocket):
    """Returns info about current logged user"""
    auth_header = websocket.headers.get('Authorization')
    token = auth_header.split(' ')[-1].strip() if auth_header else None
    if token is None:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return user.User(
            login=payload.get('sub'),
            name=payload.get('name'),
            surname=payload.get('surname'),
            roles=payload.get('roles')
        )
    except jwt.ExpiredSignatureError:
        raise expiration_exception
    except jwt.InvalidTokenError:
        raise credentials_exception


def hash_password(password: str, salt: str =settings.USER_PASSWORD_SALT) -> str:
    """Return hashed version of password"""
    return pwd_context.hash(password + salt)


def verify_password(plain_password, hashed_password, salt: str =settings.USER_PASSWORD_SALT):
    """Verifies raw and hashed password"""
    return pwd_context.verify(plain_password + salt, hashed_password)


def create_fingerprint(login: str) -> str:
    """Creates fingerprint"""
    return pwd_context.hash(login + ':' + secrets.token_hex(nbytes=32))
