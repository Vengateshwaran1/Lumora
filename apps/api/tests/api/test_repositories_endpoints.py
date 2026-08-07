"""API-level tests, hitting real Postgres + Qdrant through the FastAPI test
client. Indexing is awaited directly rather than via `BackgroundTasks`
(which fires-and-forgets after the response) — the endpoint contract is
what's under test here, not FastAPI's background-task scheduling."""

from lumora_api.api.v1.repositories import _run_indexing


async def test_register_index_status_search_chat_flow(client, sample_repo_path):
    create_response = await client.post("/api/v1/repositories", json={"url": sample_repo_path})
    assert create_response.status_code == 201
    body = create_response.json()
    repository_id = body["id"]
    assert body["status"] == "pending"
    assert body["url"] == sample_repo_path

    status_response = await client.get(f"/api/v1/repositories/{repository_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "pending"

    index_response = await client.post(f"/api/v1/repositories/{repository_id}/index")
    assert index_response.status_code == 202

    # Run the indexing job inline instead of waiting on BackgroundTasks.
    import uuid

    await _run_indexing(uuid.UUID(repository_id))

    status_response = await client.get(f"/api/v1/repositories/{repository_id}/status")
    status_body = status_response.json()
    assert status_body["status"] == "ready"
    assert status_body["indexed_file_count"] > 0
    assert status_body["indexed_chunk_count"] > 0

    search_response = await client.post(
        f"/api/v1/repositories/{repository_id}/search",
        json={"query": "greet", "top_k": 5},
    )
    assert search_response.status_code == 200
    results = search_response.json()["results"]
    assert results
    assert all("file_path" in r and "start_line" in r and "end_line" in r for r in results)

    chat_response = await client.post(
        f"/api/v1/repositories/{repository_id}/chat",
        json={"question": "What does greet do?"},
    )
    assert chat_response.status_code == 200
    chat_body = chat_response.json()
    assert chat_body["answer"]
    assert chat_body["citations"]


async def test_status_for_unknown_repository_returns_404(client):
    import uuid

    response = await client.get(f"/api/v1/repositories/{uuid.uuid4()}/status")
    assert response.status_code == 404


async def test_register_repository_rejects_empty_url(client):
    response = await client.post("/api/v1/repositories", json={"url": ""})
    assert response.status_code == 422


async def test_search_for_unknown_repository_returns_404(client):
    import uuid

    response = await client.post(f"/api/v1/repositories/{uuid.uuid4()}/search", json={"query": "x"})
    assert response.status_code == 404
