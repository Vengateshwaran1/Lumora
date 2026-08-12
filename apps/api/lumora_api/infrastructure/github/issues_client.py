"""GitHub REST client for issue sync (Milestone 3 §2). Same injectable-
`httpx.AsyncClient` pattern as `GitHubAppAuth`/`OllamaChatProvider` — unit
tests supply an `httpx.MockTransport` instead of hitting real GitHub.

Read-only: this module makes exactly one kind of call, `GET
/repos/{owner}/{repo}/issues`. Nothing here can create, edit, or comment on
anything in GitHub — see docs/architecture/adr for why the Planning Agent
(and everything upstream of it) is deliberately read-only this milestone.
"""

from dataclasses import dataclass

import httpx

_GITHUB_API_BASE_URL = "https://api.github.com"
_PER_PAGE = 100


@dataclass(frozen=True)
class GitHubIssuePayload:
    github_issue_id: int
    number: int
    title: str
    body: str | None
    author: str | None
    labels: list[str]
    state: str
    html_url: str
    created_at: str | None
    updated_at: str | None
    closed_at: str | None


class GitHubIssuesClient:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(base_url=_GITHUB_API_BASE_URL, timeout=30.0)

    async def list_issues(
        self, *, owner: str, repo: str, token: str | None, state: str = "all"
    ) -> list[GitHubIssuePayload]:
        """Fetches every open+closed issue (`state="all"`, matching what
        sync needs to keep local `state`/`closed_at` current). Unauthenticated
        for public repos (60 req/hr GitHub rate limit); `token` set uses a
        higher-limit authenticated request — never logged."""
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        issues: list[GitHubIssuePayload] = []
        page = 1
        while True:
            response = await self._client.get(
                f"/repos/{owner}/{repo}/issues",
                headers=headers,
                params={"state": state, "per_page": _PER_PAGE, "page": page},
            )
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break

            for item in batch:
                if "pull_request" in item:
                    continue  # GitHub's issues endpoint includes PRs — skip them
                issues.append(
                    GitHubIssuePayload(
                        github_issue_id=item["id"],
                        number=item["number"],
                        title=item["title"],
                        body=item.get("body"),
                        author=(item.get("user") or {}).get("login"),
                        labels=[
                            label["name"] if isinstance(label, dict) else label
                            for label in item.get("labels", [])
                        ],
                        state=item["state"],
                        html_url=item["html_url"],
                        created_at=item.get("created_at"),
                        updated_at=item.get("updated_at"),
                        closed_at=item.get("closed_at"),
                    )
                )

            if len(batch) < _PER_PAGE:
                break
            page += 1

        return issues
