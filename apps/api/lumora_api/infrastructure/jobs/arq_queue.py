"""`JobQueue` backed by arq — enqueues onto the same Redis queue the worker
process (`lumora_api.workers.settings.WorkerSettings`) consumes.

Why arq over Celery (ARCHITECTURE.md §1 names either): arq is asyncio-
native, matching the rest of the backend, and the project already depends
on Redis for the queue role §1 describes — no new datastore, no second
serialization/worker model to run alongside FastAPI's async stack.
"""

import uuid

from arq.connections import ArqRedis

from lumora_api.infrastructure.jobs.redis_events import RedisEventPublisher
from lumora_api.infrastructure.runs.run_events import RedisRunEventPublisher
from lumora_api.workers.task_names import RUN_FULL_INDEX, RUN_INCREMENTAL_INDEX, RUN_ISSUE_PLAN


class ArqJobQueue:
    def __init__(self, redis: ArqRedis) -> None:
        self._redis = redis
        # ArqRedis subclasses redis.asyncio.Redis, so the same connection
        # doubles as an EventPublisher — no second Redis client needed just
        # to publish "queued" at enqueue time.
        self._events = RedisEventPublisher(redis)
        self._run_events = RedisRunEventPublisher(redis)

    async def enqueue_full_index(self, *, repository_id: uuid.UUID) -> None:
        await self._redis.enqueue_job(RUN_FULL_INDEX, str(repository_id))
        await self._events.publish(repository_id=repository_id, event="index.queued", data={})

    async def enqueue_incremental_index(
        self,
        *,
        repository_id: uuid.UUID,
        before_sha: str | None,
        after_sha: str,
        delivery_id: uuid.UUID,
    ) -> None:
        await self._redis.enqueue_job(
            RUN_INCREMENTAL_INDEX,
            str(repository_id),
            before_sha,
            after_sha,
            str(delivery_id),
        )
        await self._events.publish(
            repository_id=repository_id, event="index.queued", data={"after_sha": after_sha}
        )

    async def enqueue_issue_plan(self, *, run_id: uuid.UUID) -> None:
        await self._redis.enqueue_job(RUN_ISSUE_PLAN, str(run_id))
        await self._run_events.publish(run_id=run_id, event="run.queued", data={})
