import asyncio
import json
from typing import Any

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore

from app.core.config import get_settings

_redis_client: Any = None
_local_cache: dict[str, str] = {}


async def get_redis():
    global _redis_client
    settings = get_settings()
    if not settings.redis_url or redis is None:
        return None
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def cache_set_json(key: str, value: dict[str, Any], ttl: int = 30) -> None:
    payload = json.dumps(value)
    client = await get_redis()
    if client:
        await client.set(key, payload, ex=ttl)
    else:
        _local_cache[key] = payload


async def cache_get_json(key: str) -> dict[str, Any] | None:
    client = await get_redis()
    raw: str | None
    if client:
        raw = await client.get(key)
    else:
        raw = _local_cache.get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
