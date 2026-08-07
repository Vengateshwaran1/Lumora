"""Search and chat use cases, exercised against real Postgres + Qdrant with
the deterministic embedding provider — indexing already has its own
end-to-end test (test_index_repository.py); these focus on retrieval and
answer generation once a repository is indexed.
"""

from lumora_api.application.chat.chat_with_repository import chat_with_repository
from lumora_api.application.indexing.index_repository import index_repository
from lumora_api.application.search.search_repository import search_repository
from lumora_api.infrastructure.llm.extractive import ExtractiveChatProvider
from lumora_api.infrastructure.models import Repository
from lumora_api.infrastructure.retrieval.reranker.noop import NoOpReranker

MAX_FILE_SIZE = 1_000_000


async def _indexed_repository(
    db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
) -> Repository:
    repository = Repository(url=sample_repo_path, name="sample")
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)

    await index_repository(
        repository_id=repository.id,
        session=db_session,
        git_service=git_service,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        max_file_size_bytes=MAX_FILE_SIZE,
    )
    await db_session.refresh(repository)
    return repository


async def test_search_returns_chunks_with_file_and_line_citations(
    db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
):
    repository = await _indexed_repository(
        db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
    )

    results = await search_repository(
        repository_id=repository.id,
        query="greet",
        top_k=5,
        session=db_session,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        reranker=NoOpReranker(),
    )

    assert results
    for chunk in results:
        assert chunk.file_path
        assert chunk.start_line >= 1
        assert chunk.end_line >= chunk.start_line

    # BM25 (lexical) should surface the exact identifier match "greet"
    # ahead of unrelated chunks, even with semantically-meaningless
    # deterministic embeddings for the dense side.
    symbols = [c.symbol for c in results]
    assert "greet" in symbols or "Greeter" in symbols


async def test_search_on_repository_with_no_chunks_returns_empty(
    db_session, deterministic_embedding_provider, vector_store
):
    repository = Repository(url="https://example.invalid/empty.git", name="empty")
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)

    results = await search_repository(
        repository_id=repository.id,
        query="anything",
        top_k=5,
        session=db_session,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        reranker=NoOpReranker(),
    )
    assert results == []


async def test_chat_returns_answer_and_citations(
    db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
):
    repository = await _indexed_repository(
        db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
    )

    answer, citations = await chat_with_repository(
        repository_id=repository.id,
        question="What does greet do?",
        session=db_session,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        reranker=NoOpReranker(),
        chat_provider=ExtractiveChatProvider(),
    )

    assert answer
    assert citations
    assert all(c.file_path and c.start_line >= 1 for c in citations)
