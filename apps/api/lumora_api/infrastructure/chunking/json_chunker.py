"""Chunks JSON objects by top-level key — line ranges are found by locating
each key's serialized token in source order, not by fixed-size windows.
Falls back to a single whole-file chunk for non-object JSON (arrays,
scalars) or when key positions can't be located (e.g. minified JSON)."""

import json

from lumora_api.domain.chunk import ChunkSpan
from lumora_api.infrastructure.chunking.base import Chunker
from lumora_api.infrastructure.chunking.utils import whole_file_span


class JsonChunker(Chunker):
    def chunk(self, content: str) -> list[ChunkSpan]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return []

        if not content.strip():
            return []

        if not isinstance(data, dict) or not data:
            return [whole_file_span(content)]

        lines = content.splitlines()
        key_positions: list[tuple[str, int]] = []
        search_from = 0
        for key in data:
            token = json.dumps(key)
            idx = content.find(token, search_from)
            if idx == -1:
                continue
            line_no = content.count("\n", 0, idx) + 1
            key_positions.append((key, line_no))
            search_from = idx + len(token)

        if not key_positions:
            return [whole_file_span(content)]

        spans: list[ChunkSpan] = []
        for i, (key, start_line) in enumerate(key_positions):
            end_line = key_positions[i + 1][1] - 1 if i + 1 < len(key_positions) else len(lines)
            end_line = max(end_line, start_line)
            spans.append(
                ChunkSpan(
                    symbol=key,
                    kind="key",
                    start_line=start_line,
                    end_line=end_line,
                    content="\n".join(lines[start_line - 1 : end_line]),
                )
            )
        return spans
