from lumora_api.domain.chunk import ChunkSpan


def whole_file_span(content: str) -> ChunkSpan:
    lines = content.splitlines()
    return ChunkSpan(
        symbol=None, kind="file", start_line=1, end_line=max(len(lines), 1), content=content
    )
