from redis import asyncio as aioredis
from app.core.config import settings

pool = aioredis.ConnectionPool.from_url(settings.REDIS_URL)
