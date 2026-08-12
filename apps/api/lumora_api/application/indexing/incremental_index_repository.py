"""Use case: process a GitHub push by diffing `last_indexed_sha → after_sha`
and re-indexing only the changed files — the Milestone 2 core pipeline.

**Base SHA comes from the database, not the webhook payload.** The
webhook's `before` field is all-zeros on branch creation, is not an
ancestor of `after` following a force-push, and — most importantly — skips
real work whenever a prior delivery was dropped or a prior job failed
partway through. `repository.last_indexed_commit` is the actual last state
we indexed, so it's the only correct diff base. If it's unset (repo never
indexed) or the fetch/diff against it fails (e.g. the commit was garbage-
collected upstream), this falls back to a full `index_repository` run —
correctness over cleverness.

**Diff source is local git, not the GitHub Compare API.** `GitService`
fetches exactly the two commits a push diff needs
(`uploadpack.allowReachableSHA1InWant`, on by default on GitHub) and reads
changed file content straight from the git object store (`git show
<sha>:<path>`) — no working-tree checkout of the whole repo, and no GitHub
API token required. That keeps the integration test for this module able
to run against a local git fixture, same as Milestone 1's ingestion tests,
without a live GitHub credential (milestone-2 spec §14).

**Idempotency**: if `after_sha` already equals `last_indexed_commit`, this
is a no-op — the same commit queued twice (e.g. two webhook deliveries
that both survived dedup because they were genuinely different delivery
IDs for the same push) does not reprocess or corrupt anything.

**Per-file fault isolation**: unlike `index_repository` (M1, single
background job, failure there fails the whole run), a webhook-triggered
job can't let one malformed file kill an otherwise-good push — each
changed file's chunk/embed step is wrapped individually; a failure is
recorded in `IncrementalIndexStats.errors` and indexing continues.

**Per-repository advisory lock** (`pg_advisory_lock`, session-scoped, held
for the whole run): two pushes seconds apart would otherwise enqueue two
overlapping jobs that read/write the same `IndexedFile`/`Chunk` rows
concurrently. Held on the same `AsyncSession` for the whole function so it
survives the per-file commits below (same pattern as M1's
`index_repository`: commit per file, not one giant transaction).
"""

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.application.indexing.file_indexer import (
    delete_file,
    index_file_content,
    rename_file_path,
)
from lumora_api.application.indexing.index_repository import index_repository
from lumora_api.application.jobs.events import EventPublisher
from lumora_api.core.config import Settings, get_settings
from lumora_api.core.time import utcnow
from lumora_api.domain.file_filter import is_safe_relative_path, looks_binary
from lumora_api.domain.git_diff import DiffEntry, DiffStatus
from lumora_api.domain.language import SUPPORTED_LANGUAGES, detect_language
from lumora_api.infrastructure.embeddings.base import EmbeddingProvider
from lumora_api.infrastructure.github.clone_auth import resolve_clone_url
from lumora_api.infrastructure.models import Chunk, IndexedFile, Repository, RepositoryStatus
from lumora_api.infrastructure.vcs.git_service import GitService
from lumora_api.infrastructure.vector_store.qdrant_store import QdrantVectorStore

logger = logging.getLogger(__name__)


@dataclass
class IncrementalIndexStats:
    base_sha: str | None
    after_sha: str
    fell_back_to_full_index: bool = False
    no_op: bool = False
    files_discovered: int = 0
    files_added: int = 0
    files_modified: int = 0
    files_renamed: int = 0
    files_deleted: int = 0
    files_skipped: int = 0
    chunks_created: int = 0  # == embedding-provider calls made (the §15 metric)
    chunks_deleted: int = 0
    errors: list[str] = field(default_factory=list)


async def incremental_index_repository(
    *,
    repository_id: uuid.UUID,
    after_sha: str,
    session: AsyncSession,
    git_service: GitService,
    embedding_provider: EmbeddingProvider,
    vector_store: QdrantVectorStore,
    max_file_size_bytes: int,
    settings: Settings | None = None,
    event_publisher: EventPublisher | None = None,
) -> IncrementalIndexStats:
    repository = await session.get(Repository, repository_id)
    if repository is None:
        raise ValueError(f"Repository {repository_id} not found")

    base_sha = repository.last_indexed_commit

    if base_sha == after_sha:
        logger.info("Repository %s already at %s — no-op", repository_id, after_sha)
        return IncrementalIndexStats(base_sha=base_sha, after_sha=after_sha, no_op=True)

    if base_sha is None or not git_service.has_clone(repository_id):
        logger.info(
            "Repository %s has no prior indexed commit or clone — falling back to full index",
            repository_id,
        )
        await index_repository(
            repository_id=repository_id,
            session=session,
            git_service=git_service,
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            max_file_size_bytes=max_file_size_bytes,
            settings=settings,
        )
        return IncrementalIndexStats(
            base_sha=base_sha, after_sha=after_sha, fell_back_to_full_index=True
        )

    await _acquire_repo_lock(session, repository_id)
    try:
        clone_url = await resolve_clone_url(repository, settings or get_settings())
        return await _run_incremental(
            repository=repository,
            clone_url=clone_url,
            base_sha=base_sha,
            after_sha=after_sha,
            session=session,
            git_service=git_service,
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            max_file_size_bytes=max_file_size_bytes,
            event_publisher=event_publisher,
        )
    finally:
        await _release_repo_lock(session, repository_id)


async def _run_incremental(
    *,
    repository: Repository,
    clone_url: str,
    base_sha: str,
    after_sha: str,
    session: AsyncSession,
    git_service: GitService,
    embedding_provider: EmbeddingProvider,
    vector_store: QdrantVectorStore,
    max_file_size_bytes: int,
    event_publisher: EventPublisher | None,
) -> IncrementalIndexStats:
    repository_id = repository.id
    stats = IncrementalIndexStats(base_sha=base_sha, after_sha=after_sha)

    repository.status = RepositoryStatus.INDEXING
    repository.index_started_at = utcnow()
    repository.index_completed_at = None
    await session.commit()

    try:
        local_path = git_service.fetch_commit(repository_id, clone_url, base_sha)
        git_service.fetch_commit(repository_id, clone_url, after_sha)
        diff_entries = git_service.diff_name_status(local_path, base_sha, after_sha)
        stats.files_discovered = len(diff_entries)
        if event_publisher is not None:
            await event_publisher.publish(
                repository_id=repository_id,
                event="index.files.discovered",
                data={
                    "count": stats.files_discovered,
                    "base_sha": base_sha,
                    "after_sha": after_sha,
                },
            )

        existing_files = await _load_existing_files(session, repository_id)

        for entry in diff_entries:
            try:
                await _process_entry(
                    entry=entry,
                    repository_id=repository_id,
                    after_sha=after_sha,
                    local_path=local_path,
                    existing_files=existing_files,
                    session=session,
                    git_service=git_service,
                    embedding_provider=embedding_provider,
                    vector_store=vector_store,
                    max_file_size_bytes=max_file_size_bytes,
                    stats=stats,
                )
                await session.commit()
                if event_publisher is not None:
                    await event_publisher.publish(
                        repository_id=repository_id,
                        event="index.file.completed",
                        data={"path": entry.path, "status": entry.status.value},
                    )
            except Exception as exc:  # noqa: BLE001 — one bad file must not kill the job
                logger.exception(
                    "Failed to process %s for repository %s", entry.path, repository_id
                )
                await session.rollback()
                stats.errors.append(f"{entry.path}: {exc}")

        repository.indexed_file_count = await _count_files(session, repository_id)
        repository.indexed_chunk_count = await _count_chunks(session, repository_id)
        repository.status = RepositoryStatus.READY
        repository.last_indexed_commit = after_sha
        repository.error_message = None
        repository.index_completed_at = utcnow()
        await session.commit()

        logger.info(
            "Incremental index for %s: %s->%s, %d files discovered, "
            "+%d ~%d -%d files (%d renamed), %d chunks embedded, %d chunks deleted, %d errors",
            repository_id,
            base_sha,
            after_sha,
            stats.files_discovered,
            stats.files_added,
            stats.files_modified,
            stats.files_deleted,
            stats.files_renamed,
            stats.chunks_created,
            stats.chunks_deleted,
            len(stats.errors),
        )
        return stats

    except Exception as exc:
        logger.exception("Incremental indexing failed for repository %s", repository_id)
        await session.rollback()
        failed_repo = await session.get(Repository, repository_id)
        if failed_repo is not None:
            failed_repo.status = RepositoryStatus.FAILED
            failed_repo.error_message = str(exc)
            failed_repo.index_completed_at = utcnow()
            await session.commit()
        raise


async def _process_entry(
    *,
    entry: DiffEntry,
    repository_id: uuid.UUID,
    after_sha: str,
    local_path: Path,
    existing_files: dict[str, IndexedFile],
    session: AsyncSession,
    git_service: GitService,
    embedding_provider: EmbeddingProvider,
    vector_store: QdrantVectorStore,
    max_file_size_bytes: int,
    stats: IncrementalIndexStats,
) -> None:
    if not is_safe_relative_path(entry.path) or (
        entry.old_path is not None and not is_safe_relative_path(entry.old_path)
    ):
        logger.warning("Skipping unsafe path in diff for repository %s: %r", repository_id, entry)
        stats.files_skipped += 1
        return

    if entry.status == DiffStatus.DELETED:
        existing = existing_files.pop(entry.path, None)
        if existing is not None:
            result = await delete_file(session, vector_store, existing)
            stats.chunks_deleted += result.chunks_deleted
            stats.files_deleted += 1
        return

    if entry.status == DiffStatus.RENAMED and entry.old_path is not None:
        existing = existing_files.pop(entry.old_path, None)
        if existing is None:
            # Old path was never indexed (unsupported language / binary /
            # too large) — treat the new path as a fresh add.
            await _add_or_modify(
                path=entry.path,
                existing_file=None,
                repository_id=repository_id,
                after_sha=after_sha,
                local_path=local_path,
                session=session,
                git_service=git_service,
                embedding_provider=embedding_provider,
                vector_store=vector_store,
                max_file_size_bytes=max_file_size_bytes,
                stats=stats,
                is_add=True,
            )
            return

        language = detect_language(entry.path)
        if language is None or language not in SUPPORTED_LANGUAGES:
            # Renamed to an extension we don't index — drop it.
            delete_result = await delete_file(session, vector_store, existing)
            stats.chunks_deleted += delete_result.chunks_deleted
            stats.files_deleted += 1
            return

        raw = git_service.read_blob(local_path, after_sha, entry.path)
        content, file_hash = _decode(raw, max_file_size_bytes)
        if content is None:
            delete_result = await delete_file(session, vector_store, existing)
            stats.chunks_deleted += delete_result.chunks_deleted
            stats.files_deleted += 1
            return

        if existing.content_hash == file_hash:
            # Pure rename — same content, so no re-embedding needed, just
            # move the path (Postgres rows + Qdrant payload).
            await rename_file_path(session, vector_store, existing, entry.path)
        else:
            index_result = await index_file_content(
                session=session,
                vector_store=vector_store,
                embedding_provider=embedding_provider,
                repository_id=repository_id,
                existing_file=existing,
                relative_path=entry.path,
                language=language,
                content=content,
                file_hash=file_hash,
            )
            stats.chunks_created += index_result.chunks_embedded
            stats.chunks_deleted += index_result.chunks_deleted
        existing_files[entry.path] = existing
        stats.files_renamed += 1
        return

    # ADDED / MODIFIED / COPIED
    existing = existing_files.get(entry.path)
    await _add_or_modify(
        path=entry.path,
        existing_file=existing,
        repository_id=repository_id,
        after_sha=after_sha,
        local_path=local_path,
        session=session,
        git_service=git_service,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        max_file_size_bytes=max_file_size_bytes,
        stats=stats,
        is_add=existing is None,
    )


async def _add_or_modify(
    *,
    path: str,
    existing_file: IndexedFile | None,
    repository_id: uuid.UUID,
    after_sha: str,
    local_path: Path,
    session: AsyncSession,
    git_service: GitService,
    embedding_provider: EmbeddingProvider,
    vector_store: QdrantVectorStore,
    max_file_size_bytes: int,
    stats: IncrementalIndexStats,
    is_add: bool,
) -> None:
    language = detect_language(path)
    if language is None or language not in SUPPORTED_LANGUAGES:
        if existing_file is not None:
            delete_result = await delete_file(session, vector_store, existing_file)
            stats.chunks_deleted += delete_result.chunks_deleted
            stats.files_deleted += 1
        else:
            stats.files_skipped += 1
        return

    raw = git_service.read_blob(local_path, after_sha, path)
    content, file_hash = _decode(raw, max_file_size_bytes)
    if content is None:
        if existing_file is not None:
            delete_result = await delete_file(session, vector_store, existing_file)
            stats.chunks_deleted += delete_result.chunks_deleted
            stats.files_deleted += 1
        else:
            stats.files_skipped += 1
        return

    if existing_file is not None and existing_file.content_hash == file_hash:
        return  # git reported a change (e.g. mode bits) but content is identical

    index_result = await index_file_content(
        session=session,
        vector_store=vector_store,
        embedding_provider=embedding_provider,
        repository_id=repository_id,
        existing_file=existing_file,
        relative_path=path,
        language=language,
        content=content,
        file_hash=file_hash,
    )
    stats.chunks_created += index_result.chunks_embedded
    stats.chunks_deleted += index_result.chunks_deleted
    if is_add:
        stats.files_added += 1
    else:
        stats.files_modified += 1


def _decode(raw: bytes | None, max_file_size_bytes: int) -> tuple[str | None, str]:
    if raw is None or len(raw) > max_file_size_bytes or looks_binary(raw):
        return None, ""
    return raw.decode("utf-8", errors="replace"), hashlib.sha256(raw).hexdigest()


async def _load_existing_files(
    session: AsyncSession, repository_id: uuid.UUID
) -> dict[str, IndexedFile]:
    result = await session.execute(
        select(IndexedFile).where(IndexedFile.repository_id == repository_id)
    )
    return {f.path: f for f in result.scalars().all()}


async def _count_files(session: AsyncSession, repository_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(IndexedFile)
        .where(IndexedFile.repository_id == repository_id)
    )
    return int(result.scalar_one())


async def _count_chunks(session: AsyncSession, repository_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.count()).select_from(Chunk).where(Chunk.repository_id == repository_id)
    )
    return int(result.scalar_one())


async def _acquire_repo_lock(session: AsyncSession, repository_id: uuid.UUID) -> None:
    await session.execute(
        text("SELECT pg_advisory_lock(hashtext(:key)::bigint)").bindparams(key=str(repository_id))
    )


async def _release_repo_lock(session: AsyncSession, repository_id: uuid.UUID) -> None:
    await session.execute(
        text("SELECT pg_advisory_unlock(hashtext(:key)::bigint)").bindparams(key=str(repository_id))
    )
