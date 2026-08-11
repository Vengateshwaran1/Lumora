"""Per-file indexing primitives shared by the full (`index_repository`) and
incremental (`incremental_index_repository`) pipelines.

Both entry points discover a *set of files to process* differently — full
indexing walks every tracked file and skips ones whose content hash is
unchanged; incremental indexing gets an explicit add/modify/delete/rename
list from a git diff — but once a path and its file content are in hand,
chunking/embedding/upserting a single file is identical work. Factoring it
here keeps that logic in one place rather than duplicated (and liable to
drift) across both use cases.
"""

import hashlib
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.domain.chunk import ChunkSpan
from lumora_api.infrastructure.chunking.registry import chunk_file
from lumora_api.infrastructure.embeddings.base import EmbeddingProvider
from lumora_api.infrastructure.models import Chunk, IndexedFile
from lumora_api.infrastructure.vector_store.qdrant_store import QdrantVectorStore, VectorPoint


@dataclass
class _PendingChunk:
    row: Chunk
    span: ChunkSpan


@dataclass(frozen=True)
class FileIndexResult:
    file_id: uuid.UUID
    total_chunks: int
    chunks_embedded: int  # actual embedding-provider calls made — the §15 metric
    chunks_deleted: int


@dataclass(frozen=True)
class FileDeleteResult:
    chunks_deleted: int


async def index_file_content(
    *,
    session: AsyncSession,
    vector_store: QdrantVectorStore,
    embedding_provider: EmbeddingProvider,
    repository_id: uuid.UUID,
    existing_file: IndexedFile | None,
    relative_path: str,
    language: str,
    content: str,
    file_hash: str,
) -> FileIndexResult:
    """Chunk `content`, embed+upsert only chunks whose content hash is new
    for this file, and delete chunks/points no longer produced. Content
    hashing (not git status) is what actually decides whether an embedding
    call happens — "modified" per git diff can still mean zero new
    embeddings if the diff only touched whitespace/comments outside chunk
    boundaries, or if a chunk's content is byte-identical to one that
    already existed elsewhere in the file."""
    spans = chunk_file(language, relative_path, content)

    if existing_file is None:
        file_row = IndexedFile(
            repository_id=repository_id,
            path=relative_path,
            language=language,
            content_hash=file_hash,
        )
        session.add(file_row)
        await session.flush()
        existing_chunks_by_hash: dict[str, Chunk] = {}
    else:
        file_row = existing_file
        file_row.path = relative_path
        file_row.language = language
        file_row.content_hash = file_hash
        result = await session.execute(select(Chunk).where(Chunk.file_id == file_row.id))
        existing_chunks_by_hash = {c.content_hash: c for c in result.scalars().all()}

    pending: list[_PendingChunk] = []
    new_hashes: set[str] = set()

    for span in spans:
        content_hash = hashlib.sha256(span.content.encode("utf-8")).hexdigest()
        new_hashes.add(content_hash)
        if content_hash in existing_chunks_by_hash:
            continue  # unchanged chunk — already embedded and stored

        chunk_id = uuid.uuid4()
        chunk_row = Chunk(
            id=chunk_id,
            repository_id=repository_id,
            file_id=file_row.id,
            file_path=relative_path,
            language=language,
            symbol=span.symbol,
            kind=span.kind,
            start_line=span.start_line,
            end_line=span.end_line,
            content=span.content,
            content_hash=content_hash,
            qdrant_point_id=str(chunk_id),
        )
        session.add(chunk_row)
        pending.append(_PendingChunk(row=chunk_row, span=span))

    stale_hashes = set(existing_chunks_by_hash) - new_hashes
    stale_point_ids = [existing_chunks_by_hash[h].qdrant_point_id for h in stale_hashes]
    for h in stale_hashes:
        await session.delete(existing_chunks_by_hash[h])

    if pending:
        vectors = await embedding_provider.embed([p.span.content for p in pending])
        await vector_store.ensure_collection(len(vectors[0]))
        points = [
            VectorPoint(
                id=str(p.row.id),
                vector=vector,
                payload={
                    "repository_id": str(repository_id),
                    "chunk_id": str(p.row.id),
                    "file_id": str(file_row.id),
                    "file_path": relative_path,
                    "language": language,
                    "symbol": p.span.symbol,
                    "kind": p.span.kind,
                    "start_line": p.span.start_line,
                    "end_line": p.span.end_line,
                    "content": p.span.content,
                    "content_hash": p.row.content_hash,
                },
            )
            for p, vector in zip(pending, vectors, strict=True)
        ]
        await vector_store.upsert(points)

    if stale_point_ids:
        await vector_store.delete(stale_point_ids)

    return FileIndexResult(
        file_id=file_row.id,
        total_chunks=len(new_hashes),
        chunks_embedded=len(pending),
        chunks_deleted=len(stale_hashes),
    )


async def delete_file(
    session: AsyncSession, vector_store: QdrantVectorStore, file_row: IndexedFile
) -> FileDeleteResult:
    """Delete an `IndexedFile` (cascades to its chunks) and the matching
    Qdrant points."""
    result = await session.execute(
        select(Chunk.qdrant_point_id).where(Chunk.file_id == file_row.id)
    )
    point_ids = list(result.scalars().all())
    await session.delete(file_row)  # cascades to chunks
    await vector_store.delete(point_ids)
    return FileDeleteResult(chunks_deleted=len(point_ids))


async def rename_file_path(
    session: AsyncSession,
    vector_store: QdrantVectorStore,
    file_row: IndexedFile,
    new_path: str,
) -> int:
    """Update a file's path (and its chunks' denormalized `file_path`, in
    Postgres and in the Qdrant payload) without touching vectors — used
    when a git rename's content hash is unchanged, so nothing needs
    re-embedding. Returns the number of chunk points updated."""
    result = await session.execute(select(Chunk).where(Chunk.file_id == file_row.id))
    chunks = result.scalars().all()

    file_row.path = new_path
    point_ids: list[str] = []
    for chunk in chunks:
        chunk.file_path = new_path
        point_ids.append(chunk.qdrant_point_id)

    await vector_store.set_payload(point_ids, {"file_path": new_path})
    return len(point_ids)
