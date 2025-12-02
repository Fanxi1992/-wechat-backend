"""
Redis client bootstrap (optional). Currently unused; initialize when Redis is needed.
"""
from typing import Optional

try:
  from redis.asyncio import Redis  # type: ignore
except ImportError:  # pragma: no cover
  Redis = None  # type: ignore

from app.core.config import settings

redis_client: Optional["Redis"] = None


async def init_redis() -> None:
  global redis_client
  if Redis is None:
    return
  redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
  )


async def get_redis() -> "Redis":
  if redis_client is None:
    raise RuntimeError("Redis is not initialized")
  return redis_client


async def close_redis() -> None:
  global redis_client
  if redis_client is not None:
    await redis_client.close()
    redis_client = None
