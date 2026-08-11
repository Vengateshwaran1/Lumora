"""Port the webhook handler and the manual-reindex endpoint depend on to
enqueue indexing work, rather than running it inline in the request
(ARCHITECTURE.md §1/§6 — indexing never runs inside FastAPI).

Real implementation: `infrastructure.jobs.arq_queue.ArqJobQueue`, backed by
arq/Redis. Tests use an in-process fake (`tests/fakes.py`) so the webhook
and endpoint tests don't need a live Redis — see
docs/architecture/milestone-2-incremental-indexing.md for why CI stays
Redis-free.
"""

import uuid
from typing import Protocol


class JobQueue(Protocol):
    async def enqueue_full_index(self, *, repository_id: uuid.UUID) -> None: ...

    async def enqueue_incremental_index(
        self,
        *,
        repository_id: uuid.UUID,
        before_sha: str | None,
        after_sha: str,
        delivery_id: uuid.UUID,
    ) -> None: ...
