"""`EventPublisher` backed by Redis pub/sub (ARCHITECTURE.md §11). See
`application.jobs.events` for why this is deliberately fire-and-forget.
"""

import json
import uuid
from typing import Any

from redis.asyncio import Redis


def channel_name(repository_id: uuid.UUID) -> str:
    return f"repo:{repository_id}:events"


class RedisEventPublisher:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def publish(self, *, repository_id: uuid.UUID, event: str, data: dict[str, Any]) -> None:
        message = json.dumps({"event": event, "data": data})
        await self._redis.publish(channel_name(repository_id), message)
