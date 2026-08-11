"""arq task functions — the actual worker-side execution of indexing jobs
enqueued by `infrastructure.jobs.arq_queue.ArqJobQueue`.

Workers run outside FastAPI, so they build their own dependencies rather
than going through `core.container`'s `Depends`-based providers — the
providers' factory functions are reused directly (same singletons, same
config), just called without the FastAPI request-scoping layer.

Lifecycle events (`index.started`/`index.completed`/`index.failed`) are
published here, at the job-boundary level; finer-grained progress
(`index.files.discovered`, `index.file.completed`) is published from
inside `incremental_index_repository` itself, which is what actually knows
when a file finishes. `index.queued` is published by `ArqJobQueue` at
enqueue time, before a worker ever picks the job up.
"""

import logging
import time
import uuid
from typing import Any

from lumora_api.application.indexing.incremental_index_repository import (
    incremental_index_repository,
)
from lumora_api.application.indexing.index_repository import index_repository
from lumora_api.core.config import get_settings
from lumora_api.core.container import get_embedding_provider, get_git_service, get_vector_store
from lumora_api.infrastructure.database import get_session_factory
from lumora_api.infrastructure.jobs.redis_events import RedisEventPublisher

logger = logging.getLogger(__name__)


async def run_full_index(ctx: dict[str, Any], repository_id_str: str) -> dict[str, Any]:
    repository_id = uuid.UUID(repository_id_str)
    settings = get_settings()
    events = RedisEventPublisher(ctx["redis"])
    session_factory = get_session_factory()

    await events.publish(repository_id=repository_id, event="index.started", data={})
    started = time.monotonic()
    try:
        async with session_factory() as session:
            await index_repository(
                repository_id=repository_id,
                session=session,
                git_service=get_git_service(),
                embedding_provider=get_embedding_provider(),
                vector_store=get_vector_store(),
                max_file_size_bytes=settings.max_file_size_bytes,
            )
    except Exception as exc:
        await events.publish(
            repository_id=repository_id, event="index.failed", data={"error": str(exc)}
        )
        raise

    await events.publish(
        repository_id=repository_id,
        event="index.completed",
        data={"duration_seconds": time.monotonic() - started},
    )
    return {"repository_id": repository_id_str}


async def run_incremental_index(
    ctx: dict[str, Any],
    repository_id_str: str,
    before_sha: str | None,
    after_sha: str,
    delivery_id_str: str,
) -> dict[str, Any]:
    del before_sha  # kept in the job signature for observability/logging only —
    # incremental_index_repository diffs from repository.last_indexed_commit,
    # never the webhook's `before` (see that module's docstring for why).
    repository_id = uuid.UUID(repository_id_str)
    settings = get_settings()
    events = RedisEventPublisher(ctx["redis"])
    session_factory = get_session_factory()

    await events.publish(
        repository_id=repository_id, event="index.started", data={"after_sha": after_sha}
    )
    started = time.monotonic()
    try:
        async with session_factory() as session:
            stats = await incremental_index_repository(
                repository_id=repository_id,
                after_sha=after_sha,
                session=session,
                git_service=get_git_service(),
                embedding_provider=get_embedding_provider(),
                vector_store=get_vector_store(),
                max_file_size_bytes=settings.max_file_size_bytes,
                event_publisher=events,
            )
    except Exception as exc:
        await events.publish(
            repository_id=repository_id, event="index.failed", data={"error": str(exc)}
        )
        raise

    duration = time.monotonic() - started
    await events.publish(
        repository_id=repository_id,
        event="index.completed",
        data={
            "duration_seconds": duration,
            "no_op": stats.no_op,
            "fell_back_to_full_index": stats.fell_back_to_full_index,
            "files_discovered": stats.files_discovered,
            "files_added": stats.files_added,
            "files_modified": stats.files_modified,
            "files_deleted": stats.files_deleted,
            "files_renamed": stats.files_renamed,
            "chunks_created": stats.chunks_created,
            "chunks_deleted": stats.chunks_deleted,
            "errors": len(stats.errors),
        },
    )
    logger.info(
        "incremental index metrics repo=%s delivery=%s duration=%.2fs "
        "files_discovered=%d chunks_created=%d chunks_deleted=%d errors=%d",
        repository_id,
        delivery_id_str,
        duration,
        stats.files_discovered,
        stats.chunks_created,
        stats.chunks_deleted,
        len(stats.errors),
    )
    return {"repository_id": repository_id_str, "delivery_id": delivery_id_str}
