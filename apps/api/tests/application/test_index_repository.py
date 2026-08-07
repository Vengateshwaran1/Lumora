"""End-to-end indexing pipeline test — the Milestone 1 gate described in
docs/architecture/ARCHITECTURE.md §5's verification section: clone → chunk
→ embed → store, exercised against real Postgres and Qdrant (no mocks),
using the deterministic embedding provider so it needs no Ollama and no
network beyond the local git fixture repo.
"""

import uuid

from sqlalchemy import select

from lumora_api.application.indexing.index_repository import index_repository
from lumora_api.infrastructure.models import Chunk, IndexedFile, Repository, RepositoryStatus

MAX_FILE_SIZE = 1_000_000


async def _register(db_session, url: str) -> Repository:
    repository = Repository(url=url, name="sample")
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)
    return repository


async def test_index_repository_populates_files_and_chunks(
    db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
):
    repository = await _register(db_session, sample_repo_path)

    await index_repository(
        repository_id=repository.id,
        session=db_session,
        git_service=git_service,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        max_file_size_bytes=MAX_FILE_SIZE,
    )

    await db_session.refresh(repository)
    assert repository.status == RepositoryStatus.READY
    assert repository.indexed_file_count == 5  # app.py, greeter.ts, README.md, config.json/yaml
    assert repository.indexed_chunk_count > 0
    assert repository.last_indexed_commit is not None
    assert repository.error_message is None

    files_result = await db_session.execute(
        select(IndexedFile).where(IndexedFile.repository_id == repository.id)
    )
    file_paths = {f.path for f in files_result.scalars().all()}
    assert file_paths == {"app.py", "greeter.ts", "README.md", "config.json", "config.yaml"}
    assert not any(p.startswith("build/") for p in file_paths)

    chunks_result = await db_session.execute(
        select(Chunk).where(Chunk.repository_id == repository.id)
    )
    chunks = chunks_result.scalars().all()
    symbols = {c.symbol for c in chunks}
    assert "Greeter" in symbols
    assert "greet" in symbols  # both the Python method and the TS function


async def test_reindexing_unchanged_repo_does_not_duplicate_chunks(
    db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
):
    repository = await _register(db_session, sample_repo_path)

    await index_repository(
        repository_id=repository.id,
        session=db_session,
        git_service=git_service,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        max_file_size_bytes=MAX_FILE_SIZE,
    )
    await db_session.refresh(repository)
    first_chunk_count = repository.indexed_chunk_count

    await index_repository(
        repository_id=repository.id,
        session=db_session,
        git_service=git_service,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        max_file_size_bytes=MAX_FILE_SIZE,
    )
    await db_session.refresh(repository)

    assert repository.indexed_chunk_count == first_chunk_count

    chunks_result = await db_session.execute(
        select(Chunk).where(Chunk.repository_id == repository.id)
    )
    assert len(chunks_result.scalars().all()) == first_chunk_count


async def test_indexing_missing_repository_raises(
    db_session, git_service, deterministic_embedding_provider, vector_store
):
    try:
        await index_repository(
            repository_id=uuid.uuid4(),
            session=db_session,
            git_service=git_service,
            embedding_provider=deterministic_embedding_provider,
            vector_store=vector_store,
            max_file_size_bytes=MAX_FILE_SIZE,
        )
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


async def test_indexing_invalid_url_marks_repository_failed(
    db_session, git_service, deterministic_embedding_provider, vector_store, tmp_path
):
    nonexistent = str(tmp_path / "does-not-exist")
    repository = await _register(db_session, nonexistent)

    try:
        await index_repository(
            repository_id=repository.id,
            session=db_session,
            git_service=git_service,
            embedding_provider=deterministic_embedding_provider,
            vector_store=vector_store,
            max_file_size_bytes=MAX_FILE_SIZE,
        )
        raise AssertionError("expected an exception for an invalid clone URL")
    except Exception:
        pass

    await db_session.refresh(repository)
    assert repository.status == RepositoryStatus.FAILED
    assert repository.error_message is not None
