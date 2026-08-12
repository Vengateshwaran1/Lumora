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
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from lumora_api.infrastructure.database import Base


class RepositoryStatus(StrEnum):
    PENDING = "pending"  # "idle" in ARCHITECTURE.md/milestone-2 wording
    QUEUED = "queued"
    CLONING = "cloning"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(2048), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    # "owner/repo" parsed from `url` at registration time (see
    # domain/repository_naming.py) — how a GitHub webhook's
    # `repository.full_name` is matched back to a row before/without a
    # GitHub App installation. Case-insensitive match at lookup time.
    full_name: Mapped[str | None] = mapped_column(String(255), default=None, index=True)
    # Populated the first time a webhook or GitHub App installation tells us
    # the repo's numeric GitHub id — preferred lookup key over `full_name`
    # once known (stable across repo renames).
    github_repo_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, default=None)
    installation_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    default_branch: Mapped[str | None] = mapped_column(String(255), default=None)
    local_path: Mapped[str | None] = mapped_column(String(1024), default=None)
    status: Mapped[RepositoryStatus] = mapped_column(String(20), default=RepositoryStatus.PENDING)
    last_indexed_commit: Mapped[str | None] = mapped_column(String(40), default=None)
    index_started_at: Mapped[datetime | None] = mapped_column(default=None)
    index_completed_at: Mapped[datetime | None] = mapped_column(default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    indexed_file_count: Mapped[int] = mapped_column(default=0)
    indexed_chunk_count: Mapped[int] = mapped_column(default=0)
    # Set by application.graph.build_symbol_graph — None means the
    # heuristic symbol_edges graph (see SymbolEdge) hasn't been built for
    # this repo yet, so the planning agent's dependency-expansion node
    # should build it lazily before expanding.
    symbol_graph_built_at: Mapped[datetime | None] = mapped_column(default=None)
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


class WebhookDeliveryStatus(StrEnum):
    RECEIVED = "received"
    IGNORED = "ignored"
    QUEUED = "queued"
    FAILED = "failed"


class WebhookDelivery(Base):
    """Dedup record for GitHub webhook deliveries (ARCHITECTURE.md §6/§8).

    `github_delivery_id` is UNIQUE — the database constraint, not an
    application-level check, is what makes dedup race-safe: two concurrent
    requests for the same delivery both attempt an insert, exactly one
    commits, the other hits `IntegrityError` and is treated as "already
    processed" (see api/webhooks.py).
    """

    __tablename__ = "webhook_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    github_delivery_id: Mapped[str] = mapped_column(String(255), unique=True)
    event_type: Mapped[str] = mapped_column(String(100))
    status: Mapped[WebhookDeliveryStatus] = mapped_column(
        String(20), default=WebhookDeliveryStatus.RECEIVED
    )
    received_at: Mapped[datetime] = mapped_column(server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(default=None)


class Issue(Base):
    """A GitHub issue synced into Lumora (Milestone 3 §2). GitHub remains
    the source of truth — this is a read cache populated by
    application.issues.sync_issues, never written back to GitHub."""

    __tablename__ = "issues"
    __table_args__ = (
        UniqueConstraint("repository_id", "github_issue_id", name="uq_issue_repo_github_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    github_issue_id: Mapped[int] = mapped_column(BigInteger)
    number: Mapped[int] = mapped_column()
    title: Mapped[str] = mapped_column(String(1024))
    body: Mapped[str | None] = mapped_column(Text, default=None)
    author: Mapped[str | None] = mapped_column(String(255), default=None)
    labels: Mapped[list[str]] = mapped_column(JSONB, default=list)
    state: Mapped[str] = mapped_column(String(20))
    html_url: Mapped[str] = mapped_column(String(2048))
    github_created_at: Mapped[datetime | None] = mapped_column(default=None)
    github_updated_at: Mapped[datetime | None] = mapped_column(default=None)
    github_closed_at: Mapped[datetime | None] = mapped_column(default=None)
    synced_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    repository: Mapped[Repository] = relationship()


class SymbolEdgeType(StrEnum):
    REFERENCES = "references"
    IMPORTS = "imports"


class SymbolEdge(Base):
    """Heuristic, Postgres-native "symbol graph" (Milestone 3 §10).

    Deliberately NOT an AST-resolved call graph — ARCHITECTURE.md §8 scopes
    that as a much larger feature, and M1/M2 explicitly deferred it. Edges
    are built by application.graph.build_symbol_graph via regex
    name-reference / import-line matching over already-chunked content, and
    are labeled as such everywhere they're surfaced (prompts, UI, docs) so
    they're never mistaken for resolved callers/callees.
    """

    __tablename__ = "symbol_edges"
    __table_args__ = (
        Index("ix_symbol_edges_repo_from", "repository_id", "from_chunk_id"),
        Index("ix_symbol_edges_repo_to", "repository_id", "to_chunk_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE")
    )
    from_chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"))
    to_chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"))
    edge_type: Mapped[SymbolEdgeType] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class RunType(StrEnum):
    PLANNING = "planning"  # only run_type in M3 — "coding" arrives in M4


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    PLAN_APPROVED = "plan_approved"
    REJECTED = "rejected"
    FAILED = "failed"


class Run(Base):
    """An agent run (Milestone 3 §4/§6, ARCHITECTURE.md §7/§8).

    `runs` is the durable source of truth the API/frontend read (same role
    Repository.status plays for indexing) — the LangGraph Postgres
    checkpointer (agents.planning.graph) is internal execution state, never
    read directly by API routes.
    """

    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    issue_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("issues.id", ondelete="SET NULL"), default=None
    )
    run_type: Mapped[RunType] = mapped_column(String(20), default=RunType.PLANNING)
    status: Mapped[RunStatus] = mapped_column(String(20), default=RunStatus.QUEUED)
    # Equal to `str(id)` — kept as its own column (rather than derived at
    # call sites) so the LangGraph thread id is explicit, greppable schema,
    # not an implicit convention.
    langgraph_thread_id: Mapped[str] = mapped_column(String(64))
    implementation_plan: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    validation_errors: Mapped[list[str]] = mapped_column(JSONB, default=list)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(default=None)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)

    repository: Mapped[Repository] = relationship()
    issue: Mapped[Issue | None] = relationship()
