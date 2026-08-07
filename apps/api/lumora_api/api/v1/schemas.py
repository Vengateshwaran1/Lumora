"""Pydantic request/response models for the repositories API.

Kept separate from the routers themselves (`repositories.py`) so the
transport-shape definitions don't crowd the endpoint logic.
"""

import uuid

from pydantic import BaseModel, Field

from lumora_api.infrastructure.models import RepositoryStatus


class CreateRepositoryRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class RepositoryStatusResponse(BaseModel):
    id: uuid.UUID
    url: str
    name: str
    status: RepositoryStatus
    default_branch: str | None
    last_indexed_commit: str | None
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
