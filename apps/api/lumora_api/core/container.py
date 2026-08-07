"""Dependency-injection providers, wired through FastAPI's `Depends`.

Lumora uses FastAPI's native dependency system rather than a standalone DI
framework: it already gives constructor-style injection, per-request
scoping, and straightforward test overrides via `app.dependency_overrides`,
which covers this project's needs without adding a second DI mechanism to
learn. This module is the single place providers are defined so routers and
services depend on functions here rather than reaching into
`core.config` / `infrastructure.database` directly.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.core.config import Settings, get_settings
from lumora_api.infrastructure.database import get_session_factory

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
