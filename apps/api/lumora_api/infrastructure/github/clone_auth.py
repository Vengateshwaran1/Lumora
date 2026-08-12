"""Resolves the URL `GitService` should actually clone/fetch from, layering
auth on top of a `Repository.url` in priority order (Milestone 3 — see
docs/architecture/adr for why a PAT fallback exists alongside the GitHub
App path): an App installation token when the repository has one, else a
configured personal access token, else the plain URL unchanged (public
repos, and every existing test fixture, which use local/SSH paths that
`authenticated_clone_url` leaves untouched).

Never logs the returned value — it embeds a bearer credential when a token
was injected. Callers should log `repository.url` (or `repository_id`) for
diagnostics, never this function's return value.
"""

from lumora_api.core.config import Settings
from lumora_api.infrastructure.github.app_auth import GitHubAppAuth, authenticated_clone_url
from lumora_api.infrastructure.models import Repository


async def resolve_clone_url(repository: Repository, settings: Settings) -> str:
    if (
        repository.installation_id is not None
        and settings.github_app_id
        and settings.github_app_private_key
    ):
        auth = GitHubAppAuth(settings.github_app_id, settings.github_app_private_key)
        token = await auth.get_installation_token(repository.installation_id)
        return authenticated_clone_url(repository.url, token)

    if settings.github_token:
        return authenticated_clone_url(repository.url, settings.github_token)

    return repository.url
