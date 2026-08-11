"""Port for publishing repository indexing progress events
(ARCHITECTURE.md §11 — Redis pub/sub, forwarded to SSE clients).

**Fire-and-forget, not durable.** There is no replay for a client that
connects after an event was published — a client that opens the SSE
stream after `index.completed` fired sees nothing further. The
`/index-status` endpoint is the source of truth the frontend reconciles
from; this exists to make an already-connected client's UI feel live, not
to guarantee delivery. Don't build retry/ack logic on top of it — if that
need shows up, it means events should move into Postgres (outbox-style),
which is a bigger change than this milestone.
"""

import uuid
from typing import Any, Protocol


class EventPublisher(Protocol):
    async def publish(
        self, *, repository_id: uuid.UUID, event: str, data: dict[str, Any]
    ) -> None: ...
