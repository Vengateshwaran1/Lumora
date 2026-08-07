"""ORM models for repository ingestion and chunk metadata.

Corresponds to a scoped-down version of the `repos` / `files` / `chunks`
tables from docs/architecture/ARCHITECTURE.md §8 — `symbol_edges` (the code
graph) is intentionally not modeled yet; Milestone 1's spec only calls for
chunk-level metadata (repository, file path, language, symbol, line range,
hash), and call-graph extraction is a separate, larger feature for a later
milestone.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from lumora_api.infrastructure.database import Base


class RepositoryStatus(StrEnum):
    PENDING = "pending"
    CLONING = "cloning"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(2048), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    default_branch: Mapped[str | None] = mapped_column(String(255), default=None)
    local_path: Mapped[str | None] = mapped_column(String(1024), default=None)
    status: Mapped[RepositoryStatus] = mapped_column(String(20), default=RepositoryStatus.PENDING)
    last_indexed_commit: Mapped[str | None] = mapped_column(String(40), default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    indexed_file_count: Mapped[int] = mapped_column(default=0)
    indexed_chunk_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    files: Mapped[list["IndexedFile"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )


class IndexedFile(Base):
    __tablename__ = "indexed_files"
    __table_args__ = (UniqueConstraint("repository_id", "path", name="uq_indexed_file_path"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    path: Mapped[str] = mapped_column(String(1024))
    language: Mapped[str | None] = mapped_column(String(50), default=None)
    content_hash: Mapped[str] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    repository: Mapped[Repository] = relationship(back_populates="files")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (Index("ix_chunk_repository_content_hash", "repository_id", "content_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("indexed_files.id", ondelete="CASCADE"), index=True
    )
    # Denormalized alongside file_id so citations and BM25 don't need a
    # join back to indexed_files for every retrieved chunk.
    file_path: Mapped[str] = mapped_column(String(1024))
    language: Mapped[str] = mapped_column(String(50))
    symbol: Mapped[str | None] = mapped_column(String(512), default=None)
    kind: Mapped[str] = mapped_column(String(20))
    start_line: Mapped[int] = mapped_column()
    end_line: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    qdrant_point_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    repository: Mapped[Repository] = relationship(back_populates="chunks")
    file: Mapped[IndexedFile] = relationship(back_populates="chunks")
