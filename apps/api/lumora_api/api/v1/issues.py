"""GitHub issue sync + Planning Agent trigger endpoints (Milestone 3 §2/§3).
Kept under the existing `/repositories` prefix (not a parallel `/repos`
prefix) — matches the repositories router's established path shape.
"""

import contextlib
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.api.v1.schemas import IssueResponse, RunSummaryResponse
from lumora_api.application.issues.sync_issues import RepositoryNotSyncableError, sync_issues
from lumora_api.core.config import get_settings
from lumora_api.core.container import DbSessionDep, GitHubIssuesClientDep, JobQueueDep
from lumora_api.infrastructure.database import get_session_factory
from lumora_api.infrastructure.github.issues_client import GitHubIssuesClient
from lumora_api.infrastructure.models import Issue, Repository, Run, RunStatus, RunType

router = APIRouter(prefix="/repositories/{repository_id}/issues", tags=["issues"])


@router.post("/sync", status_code=202)
async def trigger_sync(
    repository_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: DbSessionDep,
    client: GitHubIssuesClientDep,
) -> dict[str, str]:
    await _require_repository(session, repository_id)
    background_tasks.add_task(_run_sync, repository_id, client)
    return {"status": "syncing"}


@router.get("", response_model=list[IssueResponse])
async def list_issues(repository_id: uuid.UUID, session: DbSessionDep) -> list[Issue]:
    await _require_repository(session, repository_id)
    result = await session.execute(
        select(Issue).where(Issue.repository_id == repository_id).order_by(Issue.number.desc())
    )
    return list(result.scalars().all())


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(repository_id: uuid.UUID, issue_id: uuid.UUID, session: DbSessionDep) -> Issue:
    await _require_repository(session, repository_id)
    return await _require_issue(session, repository_id, issue_id)


@router.post("/{issue_id}/plan", response_model=RunSummaryResponse, status_code=202)
async def generate_plan(
    repository_id: uuid.UUID,
    issue_id: uuid.UUID,
    session: DbSessionDep,
    job_queue: JobQueueDep,
) -> dict[str, object]:
    await _require_repository(session, repository_id)
    await _require_issue(session, repository_id, issue_id)

    run = Run(
        repository_id=repository_id,
        issue_id=issue_id,
        run_type=RunType.PLANNING,
        status=RunStatus.QUEUED,
    )
    session.add(run)
    await session.flush()
    run.langgraph_thread_id = str(run.id)
    await session.commit()

    await job_queue.enqueue_issue_plan(run_id=run.id)
    return {"run_id": run.id, "status": run.status}


async def _require_repository(session: AsyncSession, repository_id: uuid.UUID) -> Repository:
    repository = await session.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repository


async def _require_issue(
    session: AsyncSession, repository_id: uuid.UUID, issue_id: uuid.UUID
) -> Issue:
    issue = await session.get(Issue, issue_id)
    if issue is None or issue.repository_id != repository_id:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


async def _run_sync(repository_id: uuid.UUID, client: GitHubIssuesClient) -> None:
    settings = get_settings()
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Surfaces as an empty issue list, not a 500 — logged nowhere yet.
        with contextlib.suppress(RepositoryNotSyncableError):
            await sync_issues(
                repository_id=repository_id,
                session=session,
                client=client,
                token=settings.github_token,
            )
