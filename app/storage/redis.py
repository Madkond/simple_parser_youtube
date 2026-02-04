from __future__ import annotations

from redis import Redis
from redis.asyncio import Redis as AsyncRedis


def get_redis_sync(redis_url: str) -> Redis:
    return Redis.from_url(redis_url, decode_responses=False)


def get_redis_async(redis_url: str) -> AsyncRedis:
    return AsyncRedis.from_url(redis_url, decode_responses=False)
