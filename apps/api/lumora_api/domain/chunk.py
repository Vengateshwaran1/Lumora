"""Value object for one structural chunk produced by a language chunker."""

from dataclasses import dataclass

ChunkKind = str  # "class" | "function" | "method" | "interface" | "section" | "key" | "block"


@dataclass(frozen=True)
class ChunkSpan:
    symbol: str | None
    kind: ChunkKind
    start_line: int  # 1-indexed, inclusive
    end_line: int  # 1-indexed, inclusive
    content: str
