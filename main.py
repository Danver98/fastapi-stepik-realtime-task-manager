import uvicorn
import aiohttp
from fastapi import FastAPI

from contextlib import asynccontextmanager
from app.api.endpoints.users import auth_router
from app.api.endpoints.tasks import tasks_router, websocket_router
from app.api.endpoints.errors.handlers import user_registration_error_handler
from app.api.endpoints.errors.models import UserRegistrationError


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    app.aiohttp_client_session = await aiohttp.ClientSession().__aenter__()
    yield
    if not app.aiohttp_client_session.closed:
        await app.aiohttp_client_session.__aexit__(None, None, None)


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(UserRegistrationError, handler=user_registration_error_handler)

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(websocket_router)

if __name__ == "__main__":
    uvicorn.run(app="main:app")
