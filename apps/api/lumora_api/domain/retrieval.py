"""Value object for one chunk returned by search or fed to a chat provider
as context. Shared by both so citations survive the round trip from
retrieval to the final answer unchanged."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    file_path: str
    language: str
    symbol: str | None
    kind: str
    start_line: int
    end_line: int
    content: str
    score: float
