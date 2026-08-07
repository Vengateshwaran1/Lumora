"""SQLAlchemy async engine and session factory.

No ORM models are defined yet — those, and the repositories that use this
session, land with the first feature that needs persistence (M1+). This
module only wires the connection itself, which Alembic also depends on.
"""

from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from lumora_api.core.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base — future ORM models inherit from this.

    Alembic's `env.py` points `target_metadata` at `Base.metadata`, so
    autogenerate picks up new models as soon as they're defined here.
    """


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(settings.database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=get_engine(), expire_on_commit=False)
