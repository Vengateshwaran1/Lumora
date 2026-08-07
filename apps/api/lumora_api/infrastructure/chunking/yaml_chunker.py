"""Chunks YAML mappings by top-level key, matched at column 0 to avoid
confusing a top-level key with a nested key of the same name."""

import re

import yaml

from lumora_api.domain.chunk import ChunkSpan
from lumora_api.infrastructure.chunking.base import Chunker
from lumora_api.infrastructure.chunking.utils import whole_file_span


class YamlChunker(Chunker):
    def chunk(self, content: str) -> list[ChunkSpan]:
        if not content.strip():
            return []

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError:
            return []

        if not isinstance(data, dict) or not data:
            return [whole_file_span(content)]

        lines = content.splitlines()
        key_positions: list[tuple[str, int]] = []
        for key in data:
            pattern = re.compile(rf"^{re.escape(str(key))}\s*:", re.MULTILINE)
            match = pattern.search(content)
            if match is None:
                continue
            line_no = content.count("\n", 0, match.start()) + 1
            key_positions.append((str(key), line_no))

        if not key_positions:
            return [whole_file_span(content)]

        key_positions.sort(key=lambda kp: kp[1])
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
