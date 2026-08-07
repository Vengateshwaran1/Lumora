"""Repository ingestion and RAG endpoints.

Indexing runs as a FastAPI `BackgroundTask`, not a separate worker process
— see `application.indexing.index_repository`'s module docstring and
docs/architecture/milestone-1-rag-pipeline.md for why that's the right
scope for Milestone 1 (no durable-resumable/interruptible execution need
yet) versus the full Arq/Celery worker pool §7/§12 describe for later
milestones. The background task opens its *own* DB session rather than
reusing the request-scoped one — the request-scoped session's context
manager may already be torn down by the time the background task runs.
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.api.v1.schemas import (
    ChatRequest,
    ChatResponse,
    Citation,
    CreateRepositoryRequest,
    RepositoryStatusResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from lumora_api.application.chat.chat_with_repository import chat_with_repository
from lumora_api.application.indexing.index_repository import index_repository
from lumora_api.application.repositories.create_repository import create_repository
from lumora_api.application.search.search_repository import search_repository
from lumora_api.core.config import get_settings
from lumora_api.core.container import (
    ChatProviderDep,
    DbSessionDep,
    EmbeddingProviderDep,
    RerankerDep,
    VectorStoreDep,
    get_embedding_provider,
    get_git_service,
    get_vector_store,
)
from lumora_api.infrastructure.database import get_session_factory
from lumora_api.infrastructure.models import Repository

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("", response_model=RepositoryStatusResponse, status_code=201)
async def register_repository(body: CreateRepositoryRequest, session: DbSessionDep) -> Repository:
    return await create_repository(session, body.url)


@router.post("/{repository_id}/index", response_model=RepositoryStatusResponse, status_code=202)
async def trigger_index(
    repository_id: uuid.UUID, background_tasks: BackgroundTasks, session: DbSessionDep
) -> Repository:
    repository = await session.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    background_tasks.add_task(_run_indexing, repository_id)
    return repository


@router.get("/{repository_id}/status", response_model=RepositoryStatusResponse)
async def get_status(repository_id: uuid.UUID, session: DbSessionDep) -> Repository:
    repository = await session.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repository


@router.post("/{repository_id}/search", response_model=SearchResponse)
async def search(
    repository_id: uuid.UUID,
    body: SearchRequest,
    session: DbSessionDep,
    embedding_provider: EmbeddingProviderDep,
    vector_store: VectorStoreDep,
    reranker: RerankerDep,
) -> SearchResponse:
    await _require_repository(session, repository_id)
    chunks = await search_repository(
        repository_id=repository_id,
        query=body.query,
        top_k=body.top_k,
        session=session,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        reranker=reranker,
    )
    return SearchResponse(
        results=[
            SearchResultItem(
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                language=chunk.language,
                symbol=chunk.symbol,
                kind=chunk.kind,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                score=chunk.score,
                content=chunk.content,
            )
            for chunk in chunks
        ]
    )


@router.post("/{repository_id}/chat", response_model=ChatResponse)
async def chat(
    repository_id: uuid.UUID,
    body: ChatRequest,
    session: DbSessionDep,
    embedding_provider: EmbeddingProviderDep,
    vector_store: VectorStoreDep,
    reranker: RerankerDep,
    chat_provider: ChatProviderDep,
) -> ChatResponse:
    await _require_repository(session, repository_id)
    answer, chunks = await chat_with_repository(
        repository_id=repository_id,
        question=body.question,
        session=session,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        reranker=reranker,
        chat_provider=chat_provider,
    )
    return ChatResponse(
        answer=answer,
        citations=[
            Citation(
                file_path=chunk.file_path,
                symbol=chunk.symbol,
                kind=chunk.kind,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                score=chunk.score,
            )
            for chunk in chunks
        ],
    )


async def _require_repository(session: AsyncSession, repository_id: uuid.UUID) -> Repository:
    repository = await session.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repository


async def _run_indexing(repository_id: uuid.UUID) -> None:
    settings = get_settings()
    session_factory = get_session_factory()
    async with session_factory() as session:
        await index_repository(
            repository_id=repository_id,
            session=session,
            git_service=get_git_service(),
            embedding_provider=get_embedding_provider(),
            vector_store=get_vector_store(),
            max_file_size_bytes=settings.max_file_size_bytes,
        )
