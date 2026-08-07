"""Fixed-size line-window chunker — the explicitly-allowed exception to
"never use fixed-size chunking": used only when no structural chunker
exists for a language, or a structural chunker finds nothing to split on."""

from lumora_api.domain.chunk import ChunkSpan
from lumora_api.infrastructure.chunking.base import Chunker

_DEFAULT_LINES_PER_CHUNK = 60


class FixedSizeChunker(Chunker):
    def __init__(self, lines_per_chunk: int = _DEFAULT_LINES_PER_CHUNK) -> None:
        self._lines_per_chunk = lines_per_chunk

    def chunk(self, content: str) -> list[ChunkSpan]:
        lines = content.splitlines()
        if not lines:
            return []

        spans: list[ChunkSpan] = []
        for start in range(0, len(lines), self._lines_per_chunk):
            end = min(start + self._lines_per_chunk, len(lines))
            spans.append(
                ChunkSpan(
                    symbol=None,
                    kind="block",
                    start_line=start + 1,
                    end_line=end,
                    content="\n".join(lines[start:end]),
                )
            )
        return spans
