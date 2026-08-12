"""Pydantic request/response models for the repositories API.

Kept separate from the routers themselves (`repositories.py`) so the
transport-shape definitions don't crowd the endpoint logic.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from lumora_api.infrastructure.models import RepositoryStatus, RunStatus, RunType


class CreateRepositoryRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class RepositoryStatusResponse(BaseModel):
    id: uuid.UUID
    url: str
    name: str
    full_name: str | None
    status: RepositoryStatus
    default_branch: str | None
    last_indexed_commit: str | None
    index_started_at: datetime | None
    index_completed_at: datetime | None
    indexed_file_count: int
    indexed_chunk_count: int
    error_message: str | None

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    chunk_id: str
    file_path: str
    language: str
    symbol: str | None
    kind: str
    start_line: int
    end_line: int
    score: float
    content: str


class SearchResponse(BaseModel):
    results: list[SearchResultItem]


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)


class Citation(BaseModel):
    file_path: str
    symbol: str | None
    kind: str
    start_line: int
    end_line: int
    score: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]


class IssueResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    number: int
    title: str
    body: str | None
    author: str | None
    labels: list[str]
    state: str
    html_url: str
    github_created_at: datetime | None
    github_updated_at: datetime | None
    github_closed_at: datetime | None
    synced_at: datetime

    model_config = {"from_attributes": True}


class IssueSyncResponse(BaseModel):
    created: int
    updated: int


class RunSummaryResponse(BaseModel):
    """Returned by the trigger-plan/regenerate endpoints — just enough for
    the frontend to redirect to `/app/runs/{run_id}` and start polling."""

    run_id: uuid.UUID
    status: RunStatus


class RunResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    issue_id: uuid.UUID | None
    run_type: RunType
    status: RunStatus
    implementation_plan: dict[str, Any] | None
    validation_errors: list[str]
    metrics: dict[str, Any]
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class RunDecisionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)
