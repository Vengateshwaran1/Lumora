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
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

if TYPE_CHECKING:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg_pool import AsyncConnectionPool

from arq.connections import ArqRedis
from fastapi import Depends, Request
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.application.jobs.queue import JobQueue
from lumora_api.core.config import Settings, get_settings
from lumora_api.infrastructure.database import get_session_factory
from lumora_api.infrastructure.embeddings.base import EmbeddingProvider
from lumora_api.infrastructure.embeddings.deterministic import DeterministicEmbeddingProvider
from lumora_api.infrastructure.embeddings.ollama import OllamaEmbeddingProvider
from lumora_api.infrastructure.github.issues_client import GitHubIssuesClient
from lumora_api.infrastructure.jobs.arq_queue import ArqJobQueue
from lumora_api.infrastructure.llm.base import ChatProvider
from lumora_api.infrastructure.llm.extractive import ExtractiveChatProvider
from lumora_api.infrastructure.llm.ollama import OllamaChatProvider
from lumora_api.infrastructure.llm.planning import PlanningProvider
from lumora_api.infrastructure.llm.template_planning import TemplatePlanningProvider
from lumora_api.infrastructure.retrieval.reranker.base import Reranker
from lumora_api.infrastructure.retrieval.reranker.noop import NoOpReranker
from lumora_api.infrastructure.vcs.git_service import GitService
from lumora_api.infrastructure.vector_store.qdrant_store import QdrantVectorStore

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@lru_cache
def get_git_service() -> GitService:
    settings = get_settings()
    return GitService(Path(settings.repo_storage_path))


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddingProvider(settings.ollama_base_url, settings.ollama_embedding_model)
    return DeterministicEmbeddingProvider(settings.embedding_dimensions)


@lru_cache
def get_chat_provider() -> ChatProvider:
    settings = get_settings()
    if settings.chat_provider == "ollama":
        return OllamaChatProvider(settings.ollama_base_url, settings.ollama_chat_model)
    return ExtractiveChatProvider()


@lru_cache
def get_planning_provider() -> PlanningProvider:
    settings = get_settings()
    if settings.planning_provider == "ollama":
        from lumora_api.infrastructure.llm.ollama_planning import OllamaPlanningProvider

        return OllamaPlanningProvider(settings.ollama_base_url, settings.ollama_chat_model)
    return TemplatePlanningProvider()


@lru_cache
def get_github_issues_client() -> GitHubIssuesClient:
    return GitHubIssuesClient()


@lru_cache
def get_reranker() -> Reranker:
    settings = get_settings()
    if settings.reranker_provider == "cross_encoder":
        # Deferred import — see CrossEncoderReranker's docstring for why.
        from lumora_api.infrastructure.retrieval.reranker.cross_encoder import CrossEncoderReranker

        return CrossEncoderReranker(settings.cross_encoder_model)
    return NoOpReranker()


@lru_cache
def get_vector_store() -> QdrantVectorStore:
    settings = get_settings()
    return QdrantVectorStore(settings.qdrant_url, settings.qdrant_collection)


GitServiceDep = Annotated[GitService, Depends(get_git_service)]
EmbeddingProviderDep = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]
ChatProviderDep = Annotated[ChatProvider, Depends(get_chat_provider)]
PlanningProviderDep = Annotated[PlanningProvider, Depends(get_planning_provider)]
GitHubIssuesClientDep = Annotated[GitHubIssuesClient, Depends(get_github_issues_client)]
RerankerDep = Annotated[Reranker, Depends(get_reranker)]
VectorStoreDep = Annotated[QdrantVectorStore, Depends(get_vector_store)]


async def get_arq_redis(request: Request) -> ArqRedis:
    """The arq Redis pool is created once in `main.py`'s lifespan (async
    setup, so it can't be a plain `@lru_cache` factory like the providers
    above) and stashed on `app.state` — this dependency just reads it back.
    Endpoints/tests that don't need a live Redis override `get_job_queue`/
    `get_event_publisher` directly, so this is never evaluated for them."""
    return request.app.state.arq_redis  # type: ignore[no-any-return]


ArqRedisDep = Annotated[ArqRedis, Depends(get_arq_redis)]


def get_job_queue(redis: ArqRedisDep) -> JobQueue:
    return ArqJobQueue(redis)


JobQueueDep = Annotated[JobQueue, Depends(get_job_queue)]


async def get_checkpointer(request: Request) -> BaseCheckpointSaver[Any]:
    """The LangGraph Postgres checkpointer, same `app.state`-stashed-at-
    lifespan shape as `get_arq_redis` above (its own pool + `.setup()` call
    are async, so it can't be a plain `@lru_cache` factory either). Tests
    that don't need real graph persistence override this dependency
    directly — `tests/conftest.py`'s `client` fixture runs without
    lifespan, same reason `get_job_queue` is overridden there."""
    return request.app.state.checkpointer  # type: ignore[no-any-return]


CheckpointerDep = Annotated[BaseCheckpointSaver[Any], Depends(get_checkpointer)]


async def build_checkpointer() -> tuple["AsyncConnectionPool", "AsyncPostgresSaver"]:
    """Creates the psycopg pool + `AsyncPostgresSaver` and runs its
    `.setup()` (creates LangGraph's own checkpoint tables — idempotent,
    safe to call on every process start). Called once at API startup
    (`main.py` lifespan) and once at worker startup
    (`workers/settings.py`), each with its own pool — deliberately a
    documented exception to ARCHITECTURE.md §12's "migrations never run on
    app startup": this is LangGraph-owned infrastructure, not an
    application migration, and has no separate Alembic-style deploy step
    of its own to run it from instead.

    Returns the pool alongside the saver so callers can close it at
    shutdown — `AsyncPostgresSaver` doesn't own the pool's lifecycle."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg_pool import AsyncConnectionPool

    settings = get_settings()
    pool = AsyncConnectionPool(
        conninfo=settings.psycopg_dsn,
        max_size=10,
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=False,
    )
    await pool.open()
    # psycopg_pool's default row factory is positional-tuple-typed;
    # AsyncPostgresSaver's stubs want a dict-row pool. It manages its own
    # cursors/row factory internally regardless — this is a stub mismatch,
    # not a real runtime issue.
    checkpointer = AsyncPostgresSaver(pool)  # type: ignore[arg-type]
    await checkpointer.setup()
    return pool, checkpointer
