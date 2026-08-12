"""Run-endpoint contract tests that don't need a resumable checkpoint —
see tests/agents/test_planning_graph.py for the full
generate-then-approve/reject flow through a real (in-memory) checkpointer.
"""

import uuid

from lumora_api.core.container import get_checkpointer, get_job_queue
from lumora_api.infrastructure.models import Repository, Run, RunStatus, RunType
from tests.fakes import FakeJobQueue


async def _create_run(db_session, status: RunStatus = RunStatus.QUEUED) -> Run:
    repository = Repository(url=f"https://example.invalid/{uuid.uuid4().hex}.git", name="r")
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)

    run = Run(repository_id=repository.id, run_type=RunType.PLANNING, status=status)
    db_session.add(run)
    await db_session.flush()
    run.langgraph_thread_id = str(run.id)
    await db_session.commit()
    await db_session.refresh(run)
    return run


async def test_get_run_returns_run(client, db_session):
    run = await _create_run(db_session)
    response = await client.get(f"/api/v1/runs/{run.id}")
    assert response.status_code == 200
    assert response.json()["status"] == "queued"


async def test_get_unknown_run_returns_404(client):
    response = await client.get(f"/api/v1/runs/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_approve_run_not_awaiting_approval_returns_409(app, client, db_session):
    # The route's status check runs after FastAPI resolves CheckpointerDep,
    # so it needs a value even though this test never reaches the resume
    # logic — client/app run without lifespan (see conftest.py), so
    # app.state.checkpointer is never set without this override.
    app.dependency_overrides[get_checkpointer] = lambda: None
    run = await _create_run(db_session, status=RunStatus.QUEUED)
    response = await client.post(f"/api/v1/runs/{run.id}/approve", json={})
    assert response.status_code == 409


async def test_reject_run_not_awaiting_approval_returns_409(app, client, db_session):
    app.dependency_overrides[get_checkpointer] = lambda: None
    run = await _create_run(db_session, status=RunStatus.RUNNING)
    response = await client.post(f"/api/v1/runs/{run.id}/reject", json={})
    assert response.status_code == 409


async def test_regenerate_creates_new_run_and_enqueues_it(app, client, db_session):
    fake_queue = FakeJobQueue()
    app.dependency_overrides[get_job_queue] = lambda: fake_queue
    run = await _create_run(db_session, status=RunStatus.AWAITING_APPROVAL)

    response = await client.post(f"/api/v1/runs/{run.id}/regenerate")

    assert response.status_code == 202
    body = response.json()
    new_run_id = uuid.UUID(body["run_id"])
    assert new_run_id != run.id
    assert new_run_id in fake_queue.issue_plan_calls

    # The original run is untouched — regenerate doesn't mutate it.
    original_response = await client.get(f"/api/v1/runs/{run.id}")
    assert original_response.json()["status"] == "awaiting_approval"
