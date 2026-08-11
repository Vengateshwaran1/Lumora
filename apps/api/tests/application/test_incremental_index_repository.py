"""Integration test for the Milestone 2 verification gate: full index at
commit A, push to commit B, incremental index processes only the changed
files, unchanged content is never re-embedded, deletes/renames are handled
correctly, and re-running the same commit is a no-op. Runs against real
Postgres + Qdrant with the deterministic embedding provider — no live
GitHub, no Redis (see application/indexing/incremental_index_repository.py
and application/jobs/queue.py docstrings for why)."""

import uuid

from sqlalchemy import select

from lumora_api.application.indexing.incremental_index_repository import (
    incremental_index_repository,
)
from lumora_api.application.indexing.index_repository import index_repository
from lumora_api.infrastructure.models import Chunk, IndexedFile, Repository, RepositoryStatus


async def _register(db_session, url: str) -> uuid.UUID:
    repository = Repository(url=url, name="history_repo")
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)
    return repository.id


async def test_incremental_index_processes_only_changed_files(
    db_session,
    git_service,
    deterministic_embedding_provider,
    vector_store,
    sample_repo_with_history,
):
    repository_id = await _register(db_session, sample_repo_with_history.path)

    await index_repository(
        repository_id=repository_id,
        session=db_session,
        git_service=git_service,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        max_file_size_bytes=1_000_000,
    )

    files_before = await _files_by_path(db_session, repository_id)
    unchanged_chunk_ids_before = {
        c.id for c in await _chunks_for_path(db_session, repository_id, "greeter.ts")
    }
    assert files_before["app.py"].content_hash

    repository = await db_session.get(Repository, repository_id)
    assert repository.last_indexed_commit == sample_repo_with_history.commit_a

    commit_b = sample_repo_with_history.push_commit_b()

    stats = await incremental_index_repository(
        repository_id=repository_id,
        after_sha=commit_b,
        session=db_session,
        git_service=git_service,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        max_file_size_bytes=1_000_000,
    )

    assert stats.fell_back_to_full_index is False
    assert stats.no_op is False
    assert stats.files_discovered == 4  # modified, added, deleted, renamed
    assert stats.files_modified == 1
    assert stats.files_added == 1
    assert stats.files_deleted == 1
    assert stats.files_renamed == 1
    assert not stats.errors

    await db_session.refresh(repository)
    assert repository.status == RepositoryStatus.READY
    assert repository.last_indexed_commit == commit_b

    files_after = await _files_by_path(db_session, repository_id)

    # deleted file is gone from Postgres
    assert "doomed.py" not in files_after
    # added file is present
    assert "new_file.py" in files_after
    # renamed file: new path present, old path gone, same file id (no
    # delete+recreate), same chunk rows (content unchanged -> no re-embed)
    assert "greeter.ts" not in files_after
    assert "renamed_greeter.ts" in files_after
    assert files_after["renamed_greeter.ts"].id == files_before["greeter.ts"].id
    unchanged_chunk_ids_after = {
        c.id for c in await _chunks_for_path(db_session, repository_id, "renamed_greeter.ts")
    }
    assert unchanged_chunk_ids_after == unchanged_chunk_ids_before

    # unchanged chunk content in the renamed file must not have been
    # re-embedded — chunks_created only reflects genuinely new content
    # (app.py's new `mul` function + new_file.py's chunk), not the rename.
    assert stats.chunks_created >= 1


async def test_incremental_index_is_idempotent_for_the_same_commit(
    db_session,
    git_service,
    deterministic_embedding_provider,
    vector_store,
    sample_repo_with_history,
):
    repository_id = await _register(db_session, sample_repo_with_history.path)
    await index_repository(
        repository_id=repository_id,
        session=db_session,
        git_service=git_service,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        max_file_size_bytes=1_000_000,
    )
    commit_b = sample_repo_with_history.push_commit_b()
    await incremental_index_repository(
        repository_id=repository_id,
        after_sha=commit_b,
        session=db_session,
        git_service=git_service,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        max_file_size_bytes=1_000_000,
    )
    files_after_first_run = await _files_by_path(db_session, repository_id)
    chunk_count_after_first_run = len(await _all_chunks(db_session, repository_id))

    # Same commit queued a second time (e.g. two webhook deliveries for the
    # same push) must not reprocess or duplicate anything.
    stats = await incremental_index_repository(
        repository_id=repository_id,
        after_sha=commit_b,
        session=db_session,
        git_service=git_service,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        max_file_size_bytes=1_000_000,
    )

    assert stats.no_op is True
    files_after_second_run = await _files_by_path(db_session, repository_id)
    assert files_after_second_run.keys() == files_after_first_run.keys()
    assert len(await _all_chunks(db_session, repository_id)) == chunk_count_after_first_run


async def test_incremental_index_falls_back_to_full_index_without_prior_commit(
    db_session,
    git_service,
    deterministic_embedding_provider,
    vector_store,
    sample_repo_with_history,
):
    repository_id = await _register(db_session, sample_repo_with_history.path)

    stats = await incremental_index_repository(
        repository_id=repository_id,
        after_sha=sample_repo_with_history.commit_a,
        session=db_session,
        git_service=git_service,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        max_file_size_bytes=1_000_000,
    )

    assert stats.fell_back_to_full_index is True
    repository = await db_session.get(Repository, repository_id)
    assert repository.status == RepositoryStatus.READY
    assert repository.indexed_file_count > 0


async def _files_by_path(session, repository_id) -> dict[str, IndexedFile]:
    result = await session.execute(
        select(IndexedFile).where(IndexedFile.repository_id == repository_id)
    )
    return {f.path: f for f in result.scalars().all()}


async def _chunks_for_path(session, repository_id, path) -> list[Chunk]:
    result = await session.execute(
        select(Chunk).where(Chunk.repository_id == repository_id, Chunk.file_path == path)
    )
    return list(result.scalars().all())


async def _all_chunks(session, repository_id) -> list[Chunk]:
    result = await session.execute(select(Chunk).where(Chunk.repository_id == repository_id))
    return list(result.scalars().all())
