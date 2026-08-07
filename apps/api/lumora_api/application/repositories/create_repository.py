"""Use case: register a repository. Deliberately does not clone — that
happens on the explicit POST /repositories/{id}/index call, keeping
"register" and "do the expensive work" as separate, independently
retriable steps.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.domain.repository_naming import derive_repository_name
from lumora_api.infrastructure.models import Repository


async def create_repository(session: AsyncSession, url: str) -> Repository:
    repository = Repository(url=url, name=derive_repository_name(url))
    session.add(repository)
    await session.commit()
    await session.refresh(repository)
    return repository
