import uuid

from lumora_api.application.webhooks.handle_github_webhook import PushOutcome, process_push_event
from lumora_api.application.webhooks.schemas import GitHubPushPayload
from lumora_api.infrastructure.models import Repository
from tests.fakes import FakeJobQueue


def _unique_full_name() -> str:
    # Tests share one real Postgres instance across the whole run (no
    # per-test transaction rollback), and repository lookup in
    # `process_push_event` searches by full_name globally — so every test
    # needs its own name, or an "unknown repository" test could
    # accidentally match a row a sibling test left behind.
    return f"octocat/repo-{uuid.uuid4().hex}"


def _unique_github_repo_id() -> int:
    # Same reasoning as above, for the numeric id: Postgres also persists
    # across separate `pytest` invocations (not just within one run), and
    # github_repo_id is looked up *before* full_name — small hardcoded
    # literals (1, 2, 3, ...) can collide with a leftover row from an
    # earlier run.
    return uuid.uuid4().int & 0x7FFFFFFFFFFFFFFF


async def _register(db_session, *, full_name: str) -> Repository:
    repository = Repository(
        url=f"https://github.com/{full_name}.git",
        name=full_name.split("/")[-1],
        full_name=full_name,
    )
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)
    return repository


def _payload(*, full_name: str, github_repo_id: int, **overrides) -> GitHubPushPayload:
    defaults = {
        "ref": "refs/heads/main",
        "before": "a" * 40,
        "after": "b" * 40,
        "deleted": False,
        "repository": {
            "id": github_repo_id,
            "full_name": full_name,
            "default_branch": "main",
        },
    }
    defaults.update(overrides)
    return GitHubPushPayload.model_validate(defaults)


async def test_push_on_tracked_branch_enqueues_incremental_index(db_session):
    full_name = _unique_full_name()
    repository = await _register(db_session, full_name=full_name)
    queue = FakeJobQueue()
    delivery_id = uuid.uuid4()

    result = await process_push_event(
        payload=_payload(full_name=full_name, github_repo_id=_unique_github_repo_id()),
        delivery_id=delivery_id,
        session=db_session,
        job_queue=queue,
    )

    assert result.outcome == PushOutcome.QUEUED
    assert len(queue.incremental_index_calls) == 1
    call = queue.incremental_index_calls[0]
    assert call.repository_id == repository.id
    assert call.after_sha == "b" * 40
    assert call.delivery_id == delivery_id


async def test_branch_deletion_is_ignored(db_session):
    full_name = _unique_full_name()
    await _register(db_session, full_name=full_name)
    queue = FakeJobQueue()

    result = await process_push_event(
        payload=_payload(
            full_name=full_name, github_repo_id=_unique_github_repo_id(), deleted=True
        ),
        delivery_id=uuid.uuid4(),
        session=db_session,
        job_queue=queue,
    )

    assert result.outcome == PushOutcome.IGNORED_DELETED_BRANCH
    assert not queue.incremental_index_calls


async def test_tag_push_is_ignored(db_session):
    full_name = _unique_full_name()
    await _register(db_session, full_name=full_name)
    queue = FakeJobQueue()

    result = await process_push_event(
        payload=_payload(
            full_name=full_name, github_repo_id=_unique_github_repo_id(), ref="refs/tags/v1.0.0"
        ),
        delivery_id=uuid.uuid4(),
        session=db_session,
        job_queue=queue,
    )

    assert result.outcome == PushOutcome.IGNORED_NOT_A_BRANCH
    assert not queue.incremental_index_calls


async def test_unknown_repository_is_ignored(db_session):
    queue = FakeJobQueue()

    result = await process_push_event(
        payload=_payload(full_name=_unique_full_name(), github_repo_id=_unique_github_repo_id()),
        delivery_id=uuid.uuid4(),
        session=db_session,
        job_queue=queue,
    )

    assert result.outcome == PushOutcome.IGNORED_UNKNOWN_REPOSITORY
    assert not queue.incremental_index_calls


async def test_untracked_branch_push_is_ignored(db_session):
    full_name = _unique_full_name()
    await _register(db_session, full_name=full_name)
    queue = FakeJobQueue()

    result = await process_push_event(
        payload=_payload(
            full_name=full_name, github_repo_id=_unique_github_repo_id(), ref="refs/heads/feature-x"
        ),
        delivery_id=uuid.uuid4(),
        session=db_session,
        job_queue=queue,
    )

    assert result.outcome == PushOutcome.IGNORED_UNTRACKED_BRANCH
    assert not queue.incremental_index_calls


async def test_repository_matched_case_insensitively_by_full_name(db_session):
    full_name = _unique_full_name()
    await _register(db_session, full_name=full_name.upper())
    queue = FakeJobQueue()

    result = await process_push_event(
        payload=_payload(full_name=full_name, github_repo_id=_unique_github_repo_id()),
        delivery_id=uuid.uuid4(),
        session=db_session,
        job_queue=queue,
    )

    assert result.outcome == PushOutcome.QUEUED


async def test_github_repo_id_backfilled_on_first_match(db_session):
    full_name = _unique_full_name()
    repository = await _register(db_session, full_name=full_name)
    assert repository.github_repo_id is None
    queue = FakeJobQueue()
    github_repo_id = _unique_github_repo_id()

    await process_push_event(
        payload=_payload(full_name=full_name, github_repo_id=github_repo_id),
        delivery_id=uuid.uuid4(),
        session=db_session,
        job_queue=queue,
    )

    await db_session.refresh(repository)
    assert repository.github_repo_id == github_repo_id
