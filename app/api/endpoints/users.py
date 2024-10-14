from typing import Annotated
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_session
from app.api.schemas.user import UserRegister, User
from app.services.auth_service import AuthService
from app.core.security import get_current_user, FINGERPRINT_HEADER, REFRESH_TOKEN_HEADER


auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


def get_auth_service(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    return AuthService(session)


@auth_router.post('/register')
async def register_user(request: Request,
                        auth_service: AuthService = Depends(get_auth_service)) -> User:
    form_data = await request.form()
    registered_user = UserRegister(**form_data)
    return await auth_service.register(registered_user)


@auth_router.post('/login')
async def login_user(request: Request,
                     data: Annotated[OAuth2PasswordRequestForm, Depends()],
                     auth_service: AuthService = Depends(get_auth_service)):
    access_token, refresh_token, fingerprint = await auth_service.login(data, request.headers.get(FINGERPRINT_HEADER))
    #response.headers['Authentication'] = 'Bearer ' + token
    return {
        'access_token': access_token,
        'token_type': 'Bearer',
        'logged_at': datetime.now(timezone.utc),
        'refresh_token': refresh_token,
        'fingerprint': fingerprint
    }


@auth_router.post('/logout')
async def logout_user(request: Request,
                      current_user: Annotated[User, Depends(get_current_user)],
    auth_service: AuthService = Depends(get_auth_service)) -> dict:
    await auth_service.logout(current_user.login, request.headers.get(FINGERPRINT_HEADER))
    return {
        'user': current_user.login,
        'status': 'logged out'
    }


@auth_router.post('/reissue-tokens/{login}')
async def reissue_tokens(request: Request,
                         login: str,
                         auth_service: AuthService = Depends(get_auth_service)) -> dict:
    """Reissue tokens method"""
    access_token, refresh_token, fingerprint = await auth_service.reissue_tokens(
        login,
        request.headers.get(REFRESH_TOKEN_HEADER),
        request.headers.get(FINGERPRINT_HEADER))
    return {
        'login': login,
        'access_token': access_token,
        'token_type': 'Bearer',
        'refresh_token': refresh_token,
        'fingerprint': fingerprint
    }
