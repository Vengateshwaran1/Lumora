import pytest

from lumora_api.application.issues.sync_issues import RepositoryNotSyncableError, sync_issues
from lumora_api.infrastructure.github.issues_client import GitHubIssuePayload
from lumora_api.infrastructure.models import Repository


class _StubIssuesClient:
    def __init__(self, payloads: list[GitHubIssuePayload]) -> None:
        self._payloads = payloads
        self.calls: list[tuple[str, str, str | None]] = []

    async def list_issues(self, *, owner, repo, token, state="all"):
        self.calls.append((owner, repo, token))
        return self._payloads


def _payload(**overrides) -> GitHubIssuePayload:
    defaults = dict(
        github_issue_id=1,
        number=1,
        title="Add JWT auth",
        body="body",
        author="octocat",
        labels=["enhancement"],
        state="open",
        html_url="https://github.com/o/r/issues/1",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        closed_at=None,
    )
    defaults.update(overrides)
    return GitHubIssuePayload(**defaults)


async def _repo_with_full_name(db_session, full_name: str = "o/r") -> Repository:
    repository = Repository(
        url=f"https://github.com/{full_name}.git",
        name=full_name.split("/")[-1],
        full_name=full_name,
    )
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)
    return repository


async def test_sync_issues_creates_new_issue(db_session):
    repository = await _repo_with_full_name(db_session)
    client = _StubIssuesClient([_payload()])

    stats = await sync_issues(
        repository_id=repository.id, session=db_session, client=client, token=None
    )

    assert stats.created == 1
    assert stats.updated == 0
    assert client.calls == [("o", "r", None)]


async def test_sync_issues_updates_existing_issue(db_session):
    repository = await _repo_with_full_name(db_session)
    client = _StubIssuesClient([_payload()])
    await sync_issues(repository_id=repository.id, session=db_session, client=client, token=None)

    client_v2 = _StubIssuesClient([_payload(title="Add JWT auth (updated)", state="closed")])
    stats = await sync_issues(
        repository_id=repository.id, session=db_session, client=client_v2, token=None
    )

    assert stats.created == 0
    assert stats.updated == 1


async def test_sync_issues_raises_for_unsyncable_repository(db_session):
    repository = Repository(url="/local/path/repo", name="repo")  # no derivable full_name
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)

    with pytest.raises(RepositoryNotSyncableError):
        await sync_issues(
            repository_id=repository.id,
            session=db_session,
            client=_StubIssuesClient([]),
            token=None,
        )
