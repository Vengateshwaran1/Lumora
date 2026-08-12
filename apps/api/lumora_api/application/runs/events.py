"""Port for publishing agent-run progress events — the `runs`-table
equivalent of `application.jobs.events.EventPublisher`. See that module's
docstring: fire-and-forget, not durable; `runs.status` is the source of
truth clients reconcile from.
"""

import uuid
from typing import Any, Protocol


class RunEventPublisher(Protocol):
    async def publish(self, *, run_id: uuid.UUID, event: str, data: dict[str, Any]) -> None: ...
