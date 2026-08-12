"""Use case: sync a repository's GitHub issues into the local `issues`
table (Milestone 3 §2). GitHub stays the source of truth — this upserts a
read cache, never writes back.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.core.time import utcnow
from lumora_api.infrastructure.github.issues_client import GitHubIssuePayload, GitHubIssuesClient
from lumora_api.infrastructure.models import Issue, Repository


class RepositoryNotSyncableError(Exception):
    """Raised when a repository has no derivable GitHub `owner/repo` (e.g.
    a local-path or non-GitHub URL used in tests) — issue sync needs a real
    GitHub API target."""


@dataclass
class SyncStats:
    created: int = 0
    updated: int = 0


async def sync_issues(
    *,
    repository_id: uuid.UUID,
    session: AsyncSession,
    client: GitHubIssuesClient,
    token: str | None,
) -> SyncStats:
    repository = await session.get(Repository, repository_id)
    if repository is None:
        raise ValueError(f"Repository {repository_id} not found")
    if not repository.full_name or "/" not in repository.full_name:
        raise RepositoryNotSyncableError(repository_id)

    owner, repo = repository.full_name.split("/", 1)
    payloads = await client.list_issues(owner=owner, repo=repo, token=token)

    existing_result = await session.execute(
        select(Issue).where(Issue.repository_id == repository_id)
    )
    existing_by_github_id = {issue.github_issue_id: issue for issue in existing_result.scalars()}

    stats = SyncStats()
    for payload in payloads:
        existing = existing_by_github_id.get(payload.github_issue_id)
        if existing is None:
            session.add(_new_issue(repository_id, payload))
            stats.created += 1
        else:
            _apply_payload(existing, payload)
            stats.updated += 1

    await session.commit()
    return stats


def _new_issue(repository_id: uuid.UUID, payload: GitHubIssuePayload) -> Issue:
    issue = Issue(
        repository_id=repository_id,
        github_issue_id=payload.github_issue_id,
        number=payload.number,
        title=payload.title,
        state=payload.state,
        html_url=payload.html_url,
    )
    _apply_payload(issue, payload)
    return issue


def _apply_payload(issue: Issue, payload: GitHubIssuePayload) -> None:
    issue.number = payload.number
    issue.title = payload.title
    issue.body = payload.body
    issue.author = payload.author
    issue.labels = payload.labels
    issue.state = payload.state
    issue.html_url = payload.html_url
    issue.github_created_at = _parse_timestamp(payload.created_at)
    issue.github_updated_at = _parse_timestamp(payload.updated_at)
    issue.github_closed_at = _parse_timestamp(payload.closed_at)
    issue.synced_at = utcnow()


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
