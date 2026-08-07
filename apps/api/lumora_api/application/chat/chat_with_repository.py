"""Use case: answer a question about a repository, grounded in retrieved
chunks. Composes `search_repository` rather than duplicating retrieval
logic — chat is "search, then generate," not a separate pipeline."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.application.search.search_repository import search_repository
from lumora_api.domain.retrieval import RetrievedChunk
from lumora_api.infrastructure.embeddings.base import EmbeddingProvider
from lumora_api.infrastructure.llm.base import ChatProvider
from lumora_api.infrastructure.retrieval.reranker.base import Reranker
from lumora_api.infrastructure.vector_store.qdrant_store import QdrantVectorStore

_CONTEXT_CHUNK_LIMIT = 8


async def chat_with_repository(
    *,
    repository_id: uuid.UUID,
    question: str,
    session: AsyncSession,
    embedding_provider: EmbeddingProvider,
    vector_store: QdrantVectorStore,
    reranker: Reranker,
    chat_provider: ChatProvider,
) -> tuple[str, list[RetrievedChunk]]:
    chunks = await search_repository(
        repository_id=repository_id,
        query=question,
        top_k=_CONTEXT_CHUNK_LIMIT,
        session=session,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        reranker=reranker,
    )
    answer = await chat_provider.generate_answer(question, chunks)
    return answer, chunks
