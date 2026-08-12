"""Strongly typed LangGraph state for the Planning Agent (Milestone 3 §6).

A `TypedDict`, not a raw dict — LangGraph's `StateGraph` uses this as its
schema, and every node function below takes/returns (a partial of) it,
never an untyped `dict[str, Any]`. Chunk-shaped fields are plain
`dict[str, Any]` rather than `RetrievedChunk` dataclass instances so the
Postgres checkpointer's JSON serialization has no custom-type concerns —
`agents/planning/graph.py`'s node functions convert to/from
`RetrievedChunk` at the boundary.
"""

from typing import Any, TypedDict


class RetrievedChunkDict(TypedDict):
    chunk_id: str
    file_path: str
    language: str
    symbol: str | None
    kind: str
    start_line: int
    end_line: int
    content: str
    score: float


class HistoricalIssueRef(TypedDict):
    number: int
    title: str
    html_url: str


class HistoricalCommitRef(TypedDict):
    sha: str
    subject: str


class PlannerState(TypedDict, total=False):
    run_id: str
    repository_id: str
    issue_id: str
    issue_title: str
    issue_body: str
    issue_metadata: dict[str, Any]
    issue_analysis: dict[str, Any]

    search_queries: list[str]
    retrieved_chunks: list[RetrievedChunkDict]
    related_symbols: list[RetrievedChunkDict]
    related_files: list[str]
    historical_issues: list[HistoricalIssueRef]
    historical_commits: list[HistoricalCommitRef]

    implementation_plan: dict[str, Any] | None
    risks: list[str]
    assumptions: list[str]
    confidence: float
    validation_errors: list[str]
    approval_status: str  # "pending" | "approved" | "rejected"

    metrics: dict[str, Any]
