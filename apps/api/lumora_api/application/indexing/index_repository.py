"""Use case: clone/update a repository, chunk changed files, embed new
chunks, and upsert vectors + metadata — the core Milestone 1 pipeline.

**Incremental correctness is driven by content hashing, not git diff.**
docs/architecture/ARCHITECTURE.md §6 describes a `git diff <sha>..HEAD`
approach; this simplifies it because clones here are shallow (see
`GitService`), so an old commit SHA may not exist in history to diff
against. Instead: a file whose SHA-256 hash is unchanged since the last
index is never re-parsed; a chunk whose hash already exists for that file
is never re-embedded or re-upserted. This is the concrete mechanism behind
"do not duplicate unchanged chunks."

**Commits per file, not one transaction for the whole run.** A large repo
can take a while to index; committing after each file means a crash or
error partway through preserves everything indexed so far instead of
losing it to a rollback, and `/status`'s running counts reflect real
progress instead of jumping from 0 to N at the very end.

**Known consistency caveat**: Postgres and Qdrant are two separate
datastores with no distributed transaction between them. If the process
dies between a Qdrant upsert and the following Postgres commit (or vice
versa for deletes), the two can briefly disagree for that one file. Out of
scope for M1 — an outbox/reconciliation pattern would fix it if it becomes
a real problem at higher indexing volume.

**Blocking calls run on the event loop, not `asyncio.to_thread`,** except
the two git operations (network I/O, the slowest part). Per-file
reading/hashing/chunking is CPU-light enough at M1's scope (single
background job, not high concurrency) that the added complexity of
offloading every step isn't justified yet.
"""

import asyncio
import hashlib
import logging
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.application.indexing.file_indexer import delete_file, index_file_content
from lumora_api.core.time import utcnow as _utcnow
from lumora_api.domain.file_filter import looks_binary
from lumora_api.domain.language import SUPPORTED_LANGUAGES, detect_language
from lumora_api.infrastructure.embeddings.base import EmbeddingProvider
from lumora_api.infrastructure.models import Chunk, IndexedFile, Repository, RepositoryStatus
from lumora_api.infrastructure.vcs.git_service import GitService
from lumora_api.infrastructure.vector_store.qdrant_store import QdrantVectorStore

logger = logging.getLogger(__name__)


async def index_repository(
    *,
    repository_id: uuid.UUID,
    session: AsyncSession,
    git_service: GitService,
    embedding_provider: EmbeddingProvider,
    vector_store: QdrantVectorStore,
    max_file_size_bytes: int,
) -> None:
    repository = await session.get(Repository, repository_id)
    if repository is None:
        raise ValueError(f"Repository {repository_id} not found")

    repository.status = RepositoryStatus.CLONING
    repository.index_started_at = _utcnow()
    repository.index_completed_at = None
    await session.commit()

    try:
        clone = await asyncio.to_thread(git_service.clone_or_update, repository_id, repository.url)
        repository.local_path = str(clone.local_path)
        repository.default_branch = clone.default_branch
        repository.status = RepositoryStatus.INDEXING
        await session.commit()

        tracked_paths = set(
            await asyncio.to_thread(git_service.list_tracked_files, clone.local_path)
        )

        existing_files = await _load_existing_files(session, repository_id)

        await _remove_deleted_files(session, vector_store, existing_files, tracked_paths)

        total_files = 0
        total_chunks = 0

        for relative_path in sorted(tracked_paths):
            language = detect_language(relative_path)
            if language is None or language not in SUPPORTED_LANGUAGES:
                continue

            full_path = git_service.resolve_path(clone.local_path, relative_path)
            raw = _read_file(full_path, max_file_size_bytes)
            if raw is None:
                continue

            content = raw.decode("utf-8", errors="replace")
            file_hash = hashlib.sha256(raw).hexdigest()
            existing_file = existing_files.get(relative_path)

            if existing_file is not None and existing_file.content_hash == file_hash:
                total_files += 1
                total_chunks += await _count_chunks(session, existing_file.id)
                continue

            result = await index_file_content(
                session=session,
                vector_store=vector_store,
                embedding_provider=embedding_provider,
                repository_id=repository_id,
                existing_file=existing_file,
                relative_path=relative_path,
                language=language,
                content=content,
                file_hash=file_hash,
            )
            total_files += 1
            total_chunks += result.total_chunks

            repository.indexed_file_count = total_files
            repository.indexed_chunk_count = total_chunks
            await session.commit()

        repository.status = RepositoryStatus.READY
        repository.last_indexed_commit = clone.commit_sha
        repository.indexed_file_count = total_files
        repository.indexed_chunk_count = total_chunks
        repository.error_message = None
        repository.index_completed_at = _utcnow()
        await session.commit()

    except Exception as exc:
        logger.exception("Indexing failed for repository %s", repository_id)
        await session.rollback()
        failed_repo = await session.get(Repository, repository_id)
        if failed_repo is not None:
            failed_repo.status = RepositoryStatus.FAILED
            failed_repo.error_message = str(exc)
            failed_repo.index_completed_at = _utcnow()
            await session.commit()
        raise


async def _load_existing_files(
    session: AsyncSession, repository_id: uuid.UUID
) -> dict[str, IndexedFile]:
    result = await session.execute(
        select(IndexedFile).where(IndexedFile.repository_id == repository_id)
    )
    return {f.path: f for f in result.scalars().all()}


async def _remove_deleted_files(
    session: AsyncSession,
    vector_store: QdrantVectorStore,
    existing_files: dict[str, IndexedFile],
    tracked_paths: set[str],
) -> None:
    removed_paths = set(existing_files) - tracked_paths
    if not removed_paths:
        return

    for path in removed_paths:
        file_row = existing_files.pop(path)
        await delete_file(session, vector_store, file_row)

    await session.commit()


def _read_file(full_path: Path, max_file_size_bytes: int) -> bytes | None:
    try:
        if full_path.stat().st_size > max_file_size_bytes:
            return None
        raw = full_path.read_bytes()
    except OSError:
        return None
    if looks_binary(raw):
        return None
    return raw


async def _count_chunks(session: AsyncSession, file_id: uuid.UUID) -> int:
    result = await session.execute(select(Chunk.id).where(Chunk.file_id == file_id))
    return len(result.scalars().all())
