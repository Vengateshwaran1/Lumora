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
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.core.config import Settings, get_settings
from lumora_api.infrastructure.database import get_session_factory
from lumora_api.infrastructure.embeddings.base import EmbeddingProvider
from lumora_api.infrastructure.embeddings.deterministic import DeterministicEmbeddingProvider
from lumora_api.infrastructure.embeddings.ollama import OllamaEmbeddingProvider
from lumora_api.infrastructure.llm.base import ChatProvider
from lumora_api.infrastructure.llm.extractive import ExtractiveChatProvider
from lumora_api.infrastructure.llm.ollama import OllamaChatProvider
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
RerankerDep = Annotated[Reranker, Depends(get_reranker)]
VectorStoreDep = Annotated[QdrantVectorStore, Depends(get_vector_store)]
