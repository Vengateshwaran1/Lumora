"""Use case: turn a validated GitHub `push` payload into an enqueued
incremental-indexing job (ARCHITECTURE.md §6).

Router-level concerns (raw body, HMAC verification, delivery dedup) live in
`api/webhooks.py` — this module only decides "does this push matter, and
if so, which repository/commits does it target," which is what makes it
testable without going through HTTP at all.
"""

import logging
import uuid
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.application.jobs.queue import JobQueue
from lumora_api.application.webhooks.schemas import GitHubPushPayload
from lumora_api.infrastructure.models import Repository

logger = logging.getLogger(__name__)

_BRANCH_REF_PREFIX = "refs/heads/"


class PushOutcome(StrEnum):
    QUEUED = "queued"
    IGNORED_DELETED_BRANCH = "ignored_deleted_branch"
    IGNORED_NOT_A_BRANCH = "ignored_not_a_branch"  # tag push, or other ref kind
    IGNORED_UNKNOWN_REPOSITORY = "ignored_unknown_repository"
    IGNORED_UNTRACKED_BRANCH = "ignored_untracked_branch"


@dataclass(frozen=True)
class PushResult:
    outcome: PushOutcome
    repository_id: uuid.UUID | None = None


async def process_push_event(
    *,
    payload: GitHubPushPayload,
    delivery_id: uuid.UUID,
    session: AsyncSession,
    job_queue: JobQueue,
) -> PushResult:
    if payload.deleted:
        return PushResult(outcome=PushOutcome.IGNORED_DELETED_BRANCH)

    if not payload.ref.startswith(_BRANCH_REF_PREFIX):
        # Covers tag pushes (refs/tags/...) and anything else that isn't a
        # branch — milestone-2 spec §4: only branch pushes are indexed.
        return PushResult(outcome=PushOutcome.IGNORED_NOT_A_BRANCH)

    branch = payload.ref[len(_BRANCH_REF_PREFIX) :]

    repository = await _find_repository(
        session, payload.repository.id, payload.repository.full_name
    )
    if repository is None:
        logger.info("Webhook push for unregistered repository %s", payload.repository.full_name)
        return PushResult(outcome=PushOutcome.IGNORED_UNKNOWN_REPOSITORY)

    # Opportunistically backfill identity fields once GitHub tells us them
    # — lets subsequent deliveries resolve via the faster github_repo_id
    # path, and fills in default_branch for repos M1 registered by URL
    # only (never indexed yet, so `Repository.default_branch` is NULL).
    if repository.github_repo_id is None:
        repository.github_repo_id = payload.repository.id
    if repository.full_name is None:
        repository.full_name = payload.repository.full_name

    tracked_branch = repository.default_branch or payload.repository.default_branch
    if tracked_branch is not None and branch != tracked_branch:
        await session.commit()
        return PushResult(outcome=PushOutcome.IGNORED_UNTRACKED_BRANCH, repository_id=repository.id)

    if repository.default_branch is None:
        repository.default_branch = tracked_branch

    await session.commit()

    await job_queue.enqueue_incremental_index(
        repository_id=repository.id,
        before_sha=payload.before,
        after_sha=payload.after,
        delivery_id=delivery_id,
    )
    return PushResult(outcome=PushOutcome.QUEUED, repository_id=repository.id)


async def _find_repository(
    session: AsyncSession, github_repo_id: int, full_name: str
) -> Repository | None:
    result = await session.execute(
        select(Repository).where(Repository.github_repo_id == github_repo_id)
    )
    repository = result.scalar_one_or_none()
    if repository is not None:
        return repository

    result = await session.execute(
        select(Repository).where(func.lower(Repository.full_name) == full_name.lower())
    )
    return result.scalar_one_or_none()
