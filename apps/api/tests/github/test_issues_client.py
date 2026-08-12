"""No live GitHub API is used or required — httpx.MockTransport, same
pattern as tests/github/test_app_auth.py."""

import httpx

from lumora_api.infrastructure.github.issues_client import GitHubIssuesClient

_ISSUE_JSON = {
    "id": 111,
    "number": 42,
    "title": "Add JWT auth",
    "body": "We need JWT auth.",
    "user": {"login": "octocat"},
    "labels": [{"name": "enhancement"}],
    "state": "open",
    "html_url": "https://github.com/o/r/issues/42",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
    "closed_at": None,
}

_PR_JSON = {**_ISSUE_JSON, "id": 222, "number": 43, "pull_request": {"url": "..."}}


async def test_list_issues_filters_out_pull_requests():
    def handler(request: httpx.Request) -> httpx.Response:
        page = request.url.params.get("page")
        if page == "1":
            return httpx.Response(200, json=[_ISSUE_JSON, _PR_JSON])
        return httpx.Response(200, json=[])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    issues_client = GitHubIssuesClient(client=client)

    result = await issues_client.list_issues(owner="o", repo="r", token=None)

    assert len(result) == 1
    assert result[0].number == 42
    assert result[0].labels == ["enhancement"]
    assert result[0].author == "octocat"


async def test_list_issues_sends_auth_header_when_token_given():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization")
        if request.url.params.get("page") == "1":
            return httpx.Response(200, json=[_ISSUE_JSON])
        return httpx.Response(200, json=[])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    issues_client = GitHubIssuesClient(client=client)

    await issues_client.list_issues(owner="o", repo="r", token="ghp_secret")

    assert captured["auth"] == "Bearer ghp_secret"


async def test_list_issues_paginates_until_short_page():
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        page = int(request.url.params.get("page", "1"))
        if page == 1:
            return httpx.Response(200, json=[{**_ISSUE_JSON, "id": i} for i in range(100)])
        return httpx.Response(200, json=[_ISSUE_JSON])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    issues_client = GitHubIssuesClient(client=client)

    result = await issues_client.list_issues(owner="o", repo="r", token=None)

    assert call_count == 2
    assert len(result) == 101
