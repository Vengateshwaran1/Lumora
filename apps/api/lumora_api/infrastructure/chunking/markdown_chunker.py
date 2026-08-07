"""Chunks Markdown by heading section — a structural boundary, not a parser
in the tree-sitter sense, but not fixed-size either: section length varies
with the document's own structure."""

import re

from lumora_api.domain.chunk import ChunkSpan
from lumora_api.infrastructure.chunking.base import Chunker

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


class MarkdownChunker(Chunker):
    def chunk(self, content: str) -> list[ChunkSpan]:
        lines = content.splitlines()
        headings = [
            (i + 1, m.group(2).strip())
            for i, line in enumerate(lines)
            if (m := _HEADING_RE.match(line)) is not None
        ]

        if not headings:
            if not content.strip():
                return []
            return [
                ChunkSpan(
                    symbol=None, kind="section", start_line=1, end_line=len(lines), content=content
                )
            ]

        spans: list[ChunkSpan] = []

        preamble_end = headings[0][0] - 1
        if preamble_end >= 1:
            preamble = "\n".join(lines[:preamble_end])
            if preamble.strip():
                spans.append(
                    ChunkSpan(
                        symbol=None,
                        kind="section",
                        start_line=1,
                        end_line=preamble_end,
                        content=preamble,
                    )
                )

        for i, (start_line, heading_text) in enumerate(headings):
            end_line = headings[i + 1][0] - 1 if i + 1 < len(headings) else len(lines)
            end_line = max(end_line, start_line)
            spans.append(
                ChunkSpan(
                    symbol=heading_text,
                    kind="section",
                    start_line=start_line,
                    end_line=end_line,
                    content="\n".join(lines[start_line - 1 : end_line]),
                )
            )

        return spans
