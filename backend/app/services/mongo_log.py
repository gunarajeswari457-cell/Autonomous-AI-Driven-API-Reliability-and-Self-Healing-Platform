import asyncio
from datetime import datetime, timezone
from typing import Any

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except Exception:  # pragma: no cover
    AsyncIOMotorClient = None  # type: ignore

from app.core.config import get_settings

_client: Any = None
_lock = asyncio.Lock()


async def get_mongo_db():
    global _client
    settings = get_settings()
    if not settings.mongodb_url or AsyncIOMotorClient is None:
        return None
    async with _lock:
        if _client is None:
            _client = AsyncIOMotorClient(settings.mongodb_url)
        return _client["platform"]


async def log_event(collection: str, document: dict[str, Any]) -> None:
    document = {**document, "created_at": datetime.now(timezone.utc).isoformat()}
    db = await get_mongo_db()
    if db is None:
        return
    await db[collection].insert_one(document)
