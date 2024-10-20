from typing import AsyncIterator
from redis import asyncio as aioredis
from app.db.redis_connection import pool

async def get_redis_async_session() -> AsyncIterator[aioredis.Redis]:
    """Get redis connection"""
    redis = aioredis.Redis(connection_pool=pool, decode_responses=True)
    yield redis
    await redis.close()

