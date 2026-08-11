"""HTTP-level tests for POST /webhooks/github — signature verification,
delivery dedup, and event routing through the real FastAPI app.

The queue dependency is swapped for `FakeJobQueue` for *every* test here,
including ones that never expect to reach it: FastAPI resolves all of a
route's declared dependencies before the handler body runs, so even a
request that gets rejected for a bad signature still resolves
`JobQueueDep` first. In production that's just a cheap attribute read
(`app.state.arq_redis`, set once at startup); in tests, `client`'s
`ASGITransport` never runs the app's lifespan, so that attribute doesn't
exist unless overridden — see `application/jobs/queue.py`'s docstring."""

import hashlib
import hmac
import json
import uuid

import pytest

from lumora_api.core.config import get_settings
from lumora_api.core.container import get_job_queue
from lumora_api.infrastructure.models import Repository
from tests.fakes import FakeJobQueue


@pytest.fixture
def fake_queue(app):
    queue = FakeJobQueue()
    app.dependency_overrides[get_job_queue] = lambda: queue
    return queue


def _sign(body: bytes) -> str:
    secret = get_settings().github_webhook_secret
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _push_body(*, full_name: str, github_repo_id: int, ref: str = "refs/heads/main") -> bytes:
    payload = {
        "ref": ref,
        "before": "a" * 40,
        "after": "b" * 40,
        "deleted": False,
        "repository": {"id": github_repo_id, "full_name": full_name, "default_branch": "main"},
    }
    return json.dumps(payload).encode()


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


def _unique_full_name() -> str:
    return f"octocat/repo-{uuid.uuid4().hex}"


def _unique_github_repo_id() -> int:
    # Postgres isn't truncated between separate `pytest` invocations, and
    # `github_repo_id` is looked up before `full_name` — a small hardcoded
    # literal here can collide with a leftover row from an earlier run and
    # silently match the wrong repository.
    return uuid.uuid4().int & 0x7FFFFFFFFFFFFFFF


async def test_missing_signature_rejected(client, fake_queue):
    response = await client.post(
        "/webhooks/github",
        content=b"{}",
        headers={"X-GitHub-Event": "push", "X-GitHub-Delivery": str(uuid.uuid4())},
    )
    assert response.status_code == 401


async def test_wrong_signature_rejected(client, fake_queue):
    body = b"{}"
    response = await client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": "sha256=" + "0" * 64,
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 401


async def test_missing_delivery_header_rejected(client, fake_queue):
    body = b"{}"
    response = await client.post(
        "/webhooks/github",
        content=body,
        headers={"X-Hub-Signature-256": _sign(body), "X-GitHub-Event": "push"},
    )
    assert response.status_code == 400


async def test_unsupported_event_acknowledged_without_enqueue(client, db_session, fake_queue):
    full_name = _unique_full_name()
    await _register(db_session, full_name=full_name)
    body = _push_body(full_name=full_name, github_repo_id=_unique_github_repo_id())

    response = await client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body),
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 200
    assert not fake_queue.incremental_index_calls


async def test_valid_push_enqueues_incremental_index(client, db_session, fake_queue):
    full_name = _unique_full_name()
    repository = await _register(db_session, full_name=full_name)
    body = _push_body(full_name=full_name, github_repo_id=_unique_github_repo_id())

    response = await client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body),
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 200
    assert len(fake_queue.incremental_index_calls) == 1
    assert fake_queue.incremental_index_calls[0].repository_id == repository.id


async def test_duplicate_delivery_id_does_not_enqueue_twice(client, db_session, fake_queue):
    full_name = _unique_full_name()
    await _register(db_session, full_name=full_name)
    body = _push_body(full_name=full_name, github_repo_id=_unique_github_repo_id())
    delivery_id = str(uuid.uuid4())
    headers = {
        "X-Hub-Signature-256": _sign(body),
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": delivery_id,
    }

    first = await client.post("/webhooks/github", content=body, headers=headers)
    second = await client.post("/webhooks/github", content=body, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(fake_queue.incremental_index_calls) == 1


async def test_untracked_branch_push_acknowledged_without_enqueue(client, db_session, fake_queue):
    full_name = _unique_full_name()
    await _register(db_session, full_name=full_name)
    body = _push_body(
        full_name=full_name, github_repo_id=_unique_github_repo_id(), ref="refs/heads/feature-x"
    )

    response = await client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body),
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 200
    assert not fake_queue.incremental_index_calls
