import uuid

import pytest

from lumora_api.core.container import get_job_queue
from tests.fakes import FakeJobQueue


@pytest.fixture
def fake_queue(app):
    # /reindex declares JobQueueDep, and FastAPI resolves every declared
    # dependency before the handler body runs — including for the 404 case
    # below, before `_require_repository` ever gets a chance to short-
    # circuit. See tests/api/test_webhooks_endpoint.py's module docstring
    # for the same eager-resolution behavior on the webhook route.
    queue = FakeJobQueue()
    app.dependency_overrides[get_job_queue] = lambda: queue
    return queue


async def test_get_repository_returns_full_resource(client, sample_repo_path):
    create_response = await client.post("/api/v1/repositories", json={"url": sample_repo_path})
    repository_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/repositories/{repository_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == repository_id
    assert body["status"] == "pending"
    assert "index_started_at" in body
    assert "index_completed_at" in body


async def test_get_repository_unknown_returns_404(client):
    response = await client.get(f"/api/v1/repositories/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_index_status_alias_matches_status(client, sample_repo_path):
    create_response = await client.post("/api/v1/repositories", json={"url": sample_repo_path})
    repository_id = create_response.json()["id"]

    status_response = await client.get(f"/api/v1/repositories/{repository_id}/status")
    index_status_response = await client.get(f"/api/v1/repositories/{repository_id}/index-status")

    assert index_status_response.status_code == 200
    assert index_status_response.json() == status_response.json()


async def test_reindex_enqueues_a_full_index_job(client, fake_queue, sample_repo_path):
    from lumora_api.api.v1.repositories import _run_indexing

    create_response = await client.post("/api/v1/repositories", json={"url": sample_repo_path})
    repository_id = create_response.json()["id"]

    reindex_response = await client.post(f"/api/v1/repositories/{repository_id}/reindex")
    assert reindex_response.status_code == 202
    assert fake_queue.full_index_calls == [uuid.UUID(repository_id)]

    # Simulate the worker picking the job up (real end-to-end coverage of
    # run_full_index -> index_repository lives in the arq worker itself).
    await _run_indexing(uuid.UUID(repository_id))

    status_response = await client.get(f"/api/v1/repositories/{repository_id}/status")
    body = status_response.json()
    assert body["status"] == "ready"
    assert body["indexed_file_count"] > 0


async def test_reindex_unknown_repository_returns_404(client, fake_queue):
    response = await client.post(f"/api/v1/repositories/{uuid.uuid4()}/reindex")
    assert response.status_code == 404
