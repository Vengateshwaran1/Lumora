import uuid

from lumora_api.api.v1.issues import _run_sync
from lumora_api.core.container import get_github_issues_client, get_job_queue
from lumora_api.infrastructure.github.issues_client import GitHubIssuePayload
from tests.fakes import FakeJobQueue


class _StubIssuesClient:
    def __init__(self, payloads):
        self._payloads = payloads

    async def list_issues(self, *, owner, repo, token, state="all"):
        return self._payloads


_PAYLOAD = GitHubIssuePayload(
    github_issue_id=1,
    number=7,
    title="Add JWT auth",
    body="We need JWT auth for the API.",
    author="octocat",
    labels=["enhancement"],
    state="open",
    html_url="https://github.com/o/r/issues/7",
    created_at="2026-01-01T00:00:00Z",
    updated_at="2026-01-01T00:00:00Z",
    closed_at=None,
)


async def _register_repo(client, url="https://github.com/o/r.git"):
    response = await client.post("/api/v1/repositories", json={"url": url})
    return response.json()["id"]


async def test_sync_then_list_issues(app, client):
    # Overriding the DI'd client isn't just belt-and-suspenders here: the
    # endpoint's BackgroundTask would otherwise hit the real GitHub API
    # with whatever the default client resolves to.
    app.dependency_overrides[get_github_issues_client] = lambda: _StubIssuesClient([_PAYLOAD])
    repository_id = await _register_repo(client)

    sync_response = await client.post(f"/api/v1/repositories/{repository_id}/issues/sync")
    assert sync_response.status_code == 202

    # Run the sync inline too, for a deterministic assertion point instead
    # of relying on BackgroundTasks scheduling — same pattern
    # test_repositories_endpoints.py uses for /index.
    await _run_sync(uuid.UUID(repository_id), _StubIssuesClient([_PAYLOAD]))

    list_response = await client.get(f"/api/v1/repositories/{repository_id}/issues")
    assert list_response.status_code == 200
    issues = list_response.json()
    assert len(issues) == 1
    assert issues[0]["number"] == 7
    assert issues[0]["title"] == "Add JWT auth"


async def test_get_issue_not_found_returns_404(client):
    repository_id = await _register_repo(client)
    response = await client.get(f"/api/v1/repositories/{repository_id}/issues/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_generate_plan_enqueues_run_and_returns_202(app, client):
    fake_queue = FakeJobQueue()
    app.dependency_overrides[get_job_queue] = lambda: fake_queue

    repository_id = await _register_repo(client)
    await _run_sync(uuid.UUID(repository_id), _StubIssuesClient([_PAYLOAD]))
    issue_id = (await client.get(f"/api/v1/repositories/{repository_id}/issues")).json()[0]["id"]

    response = await client.post(f"/api/v1/repositories/{repository_id}/issues/{issue_id}/plan")

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert uuid.UUID(body["run_id"]) in fake_queue.issue_plan_calls


async def test_generate_plan_for_unknown_issue_returns_404(client):
    repository_id = await _register_repo(client)
    response = await client.post(f"/api/v1/repositories/{repository_id}/issues/{uuid.uuid4()}/plan")
    assert response.status_code == 404
