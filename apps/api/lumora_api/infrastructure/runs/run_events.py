"""`EventPublisher`-shaped Redis pub/sub for run progress — same
fire-and-forget shape as `infrastructure.jobs.redis_events`, just keyed on
`run_id` instead of `repository_id` (Milestone 3 §20 reuses the existing
SSE infrastructure rather than building a second mechanism). `runs` (the
Postgres table) is the durable source of truth; this only decorates an
already-open SSE connection — see that module's docstring for the same
caveat applied here.
"""

import json
import uuid
from typing import Any

from redis.asyncio import Redis


def run_channel_name(run_id: uuid.UUID) -> str:
    return f"run:{run_id}:events"


class RedisRunEventPublisher:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def publish(self, *, run_id: uuid.UUID, event: str, data: dict[str, Any]) -> None:
        message = json.dumps({"event": event, "data": data})
        await self._redis.publish(run_channel_name(run_id), message)
