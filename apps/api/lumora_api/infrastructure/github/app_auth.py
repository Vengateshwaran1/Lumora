"""GitHub App authentication (ARCHITECTURE.md §9): mint a short-lived JWT
signed with the App's private key, then exchange it for an installation
access token scoped to one installation. Used only when a repository has
an `installation_id` and the app has `GITHUB_APP_ID`/
`GITHUB_APP_PRIVATE_KEY` configured — public repos and local/CI testing
clone via the repository's plain `url` instead (M1 behavior; see
docs/architecture/milestone-2-incremental-indexing.md for why this path
has no live-credential test coverage).

Never logs the app JWT or the installation token — both are bearer
credentials for the lifetime of their expiry.
"""

import time

import httpx
import jwt

_JWT_CLOCK_SKEW_SECONDS = 60
_JWT_TTL_SECONDS = 540  # GitHub caps App JWTs at 10 minutes; stay under it
_GITHUB_API_BASE_URL = "https://api.github.com"


class GitHubAppAuth:
    """`client` is injectable so unit tests can supply an
    `httpx.MockTransport` instead of requiring real GitHub App
    credentials — same pattern as `OllamaEmbeddingProvider`."""

    def __init__(
        self, app_id: str, private_key_pem: str, client: httpx.AsyncClient | None = None
    ) -> None:
        self._app_id = app_id
        self._private_key_pem = private_key_pem
        self._client = client or httpx.AsyncClient(base_url=_GITHUB_API_BASE_URL, timeout=30.0)

    def _app_jwt(self) -> str:
        now = int(time.time())
        payload = {
            "iat": now - _JWT_CLOCK_SKEW_SECONDS,
            "exp": now + _JWT_TTL_SECONDS,
            "iss": self._app_id,
        }
        return jwt.encode(payload, self._private_key_pem, algorithm="RS256")

    async def get_installation_token(self, installation_id: int) -> str:
        """Returns a token valid for ~1 hour, scoped to whatever repos/
        permissions the installation grants. Callers should mint a fresh
        one per job rather than caching — the cost is one extra HTTP call
        against a token lifetime measured in indexing-job minutes."""
        response = await self._client.post(
            f"/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {self._app_jwt()}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
        token = response.json()["token"]
        if not isinstance(token, str):
            raise ValueError("GitHub installation token response missing 'token'")
        return token


def authenticated_clone_url(url: str, token: str) -> str:
    """Injects a GitHub App installation token into an HTTPS clone URL —
    `https://x-access-token:<token>@github.com/owner/repo.git`, the form
    GitHub's own docs specify for installation-token clones. Returns
    `url` unchanged if it isn't an `https://` URL (SSH/local-path URLs,
    used throughout this project's tests, have no token to inject)."""
    if not url.startswith("https://"):
        return url
    return url.replace("https://", f"https://x-access-token:{token}@", 1)
