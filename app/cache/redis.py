"""redis.py"""

import os
from typing import Tuple

import redis
from redis import asyncio as aioredis

from app.core.config import settings
from cache.enums import RedisStatus


# for ws
async def redis_connect_async(timeout: int = None) -> aioredis.Redis:
    client = aioredis.from_url(
        str(settings.REDIS_URI),
        # timeout=timeout,
        decode_responses=True,
    )
    return client


async def redis_connect(
    host_url: str,
) -> Tuple[RedisStatus, aioredis.client.Redis]:
    """Attempt to connect to `host_url` and return a Redis client instance if successful."""
    return (
        await _connect(host_url)
        if os.environ.get("CACHE_ENV") != "TEST"
        else _connect_fake()
    )


async def _connect(
    host_url: str,
) -> tuple[RedisStatus, aioredis.client.Redis]:  # pragma: no cover
    try:
        redis_client = await aioredis.from_url(host_url)
        if await redis_client.ping():
            return (RedisStatus.CONNECTED, redis_client)
        return (RedisStatus.CONN_ERROR, None)
    except aioredis.AuthenticationError:
        return (RedisStatus.AUTH_ERROR, None)
    except aioredis.ConnectionError:
        return (RedisStatus.CONN_ERROR, None)


def redis_connect_sync() -> redis.client.Redis:
    # client = redis.Redis(
    #     host=settings.REDIS_SERVER,
    #     port=settings.REDIS_PORT,
    #     password=settings.REDIS_PASSWORD,
    #     db=settings.REDIS_DB,
    #     socket_timeout=settings.REDIS_TIMEOUT,
    #     decode_responses=True,
    # )
    client = redis.from_url(str(settings.REDIS_URI))
    # ping = client.ping()
    # if ping is True:
    return client


redis_client = redis_connect_sync()


def _connect_fake() -> Tuple[RedisStatus, aioredis.client.Redis]:
    from fakeredis import FakeRedis

    return (RedisStatus.CONNECTED, FakeRedis())
