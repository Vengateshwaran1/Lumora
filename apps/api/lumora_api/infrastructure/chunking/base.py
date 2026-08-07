"""Chunker abstraction — one implementation per language family.

`Chunker.chunk` never raises for well-formed-enough input; a chunker that
can't find anything structural to split on returns an empty list, and
callers fall back to `FixedSizeChunker` (see `registry.py`) — this is the
"never use fixed-size chunking unless no parser exists" rule made concrete.
"""

from abc import ABC, abstractmethod

from lumora_api.domain.chunk import ChunkSpan


class Chunker(ABC):
    @abstractmethod
    def chunk(self, content: str) -> list[ChunkSpan]:
        """Split source text into structural chunks."""
