"""
    Global conftest file for tests
"""
from typing import AsyncIterator, AsyncGenerator
from redis.asyncio import Redis, ConnectionPool
import pytest_asyncio
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.base import Base
from app.db.database import get_async_session
from app.db.redis import get_redis_async_session

from main import app

# Database
engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=True, poolclass=NullPool)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession)
# Redis
pool = ConnectionPool.from_url(settings.REDIS_URL)


@pytest_asyncio.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop.. Hack when starting all tests at once"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True, scope="session")
async def prepare_database():
    """Set up and tear down database for tests"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(autouse=True, scope="session")
async def clear_redis():
    """Clear redis sessions"""
    yield
    redis = Redis(connection_pool=pool, decode_responses=True)
    redis.flushdb()
    redis.close()


async def get_async_session_override() -> AsyncIterator[AsyncSession]:
    """Override async session for tests"""
    async with async_session_maker() as session:
        yield session


async def get_redis_async_session_override() -> AsyncIterator[Redis]:
    """Override async redis session for tests"""
    redis = Redis(connection_pool=pool, decode_responses=True)
    yield redis
    await redis.close()


app.dependency_overrides[get_async_session] = get_async_session_override
app.dependency_overrides[get_redis_async_session] = get_redis_async_session_override
client = TestClient(app)


@pytest_asyncio.fixture(name="async_client", scope="session")
async def async_client_fixture() -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for async tests"""
    async with AsyncClient(app=app, base_url=settings.BASE_URL) as ac:
        yield ac
