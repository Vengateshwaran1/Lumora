"""In-process fakes for ports that would otherwise require a live Redis —
see application/jobs/queue.py's module docstring for why webhook/endpoint
tests use these instead of a real arq-backed queue."""

import uuid
from dataclasses import dataclass, field


@dataclass
class EnqueuedIncrementalIndex:
    repository_id: uuid.UUID
    before_sha: str | None
    after_sha: str
    delivery_id: uuid.UUID


@dataclass
class FakeJobQueue:
    full_index_calls: list[uuid.UUID] = field(default_factory=list)
    incremental_index_calls: list[EnqueuedIncrementalIndex] = field(default_factory=list)
    issue_plan_calls: list[uuid.UUID] = field(default_factory=list)

    async def enqueue_full_index(self, *, repository_id: uuid.UUID) -> None:
        self.full_index_calls.append(repository_id)

    async def enqueue_incremental_index(
        self,
        *,
        repository_id: uuid.UUID,
        before_sha: str | None,
        after_sha: str,
        delivery_id: uuid.UUID,
    ) -> None:
        self.incremental_index_calls.append(
            EnqueuedIncrementalIndex(
                repository_id=repository_id,
                before_sha=before_sha,
                after_sha=after_sha,
                delivery_id=delivery_id,
            )
        )

    async def enqueue_issue_plan(self, *, run_id: uuid.UUID) -> None:
        self.issue_plan_calls.append(run_id)
