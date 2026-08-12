"""Use case: register a repository. Deliberately does not clone — that
happens on the explicit POST /repositories/{id}/index call, keeping
"register" and "do the expensive work" as separate, independently
retriable steps.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.domain.repository_naming import derive_full_name, derive_repository_name
from lumora_api.infrastructure.models import Repository


class RepositoryAlreadyExistsError(Exception):
    """Raised when `url` is already registered — `Repository.url` is
    UNIQUE, so this turns a double-click "Connect" or a re-registration
    attempt into a clear 409 (see api/v1/repositories.py) instead of an
    unhandled 500."""


async def create_repository(session: AsyncSession, url: str) -> Repository:
    repository = Repository(
        url=url, name=derive_repository_name(url), full_name=derive_full_name(url)
    )
    session.add(repository)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise RepositoryAlreadyExistsError(url) from exc
    await session.refresh(repository)
    return repository
