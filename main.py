import uvicorn
from fastapi import FastAPI
from redis.exceptions import RedisClusterException, RedisError
from app.api.endpoints.users import auth_router
from app.api.endpoints.tasks import tasks_router, websocket_router
from app.api.endpoints.errors.handlers import user_registration_error_handler, redis_error_handler
from app.api.endpoints.errors.models import UserRegistrationError
from app.api.middleware import logging_middleware


app = FastAPI()

app.add_exception_handler(UserRegistrationError, handler=user_registration_error_handler)
app.add_exception_handler(RedisError, handler=redis_error_handler)
app.add_exception_handler(RedisClusterException, handler=redis_error_handler)

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(websocket_router)

app.middleware("http")(logging_middleware)

if __name__ == "__main__":
    uvicorn.run(app="main:app")
