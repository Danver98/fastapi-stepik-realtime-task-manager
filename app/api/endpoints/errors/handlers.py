from fastapi import Request, status
from fastapi.responses import JSONResponse
from .models import UserRegistrationError


async def user_registration_error_handler(_: Request, ex: UserRegistrationError) -> JSONResponse:
    """User registration error handler"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            'message': ex.message
        }
    )