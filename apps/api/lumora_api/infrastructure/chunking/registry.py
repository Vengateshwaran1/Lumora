"""Selects a chunker for a (language, path) pair and applies the
fixed-size fallback when no structural chunker exists or the structural
chunker finds nothing (e.g. a source file with no top-level declarations).
"""

from lumora_api.domain.chunk import ChunkSpan
from lumora_api.infrastructure.chunking.base import Chunker
from lumora_api.infrastructure.chunking.fallback import FixedSizeChunker
from lumora_api.infrastructure.chunking.js_ts_chunker import JsTsChunker
from lumora_api.infrastructure.chunking.json_chunker import JsonChunker
from lumora_api.infrastructure.chunking.markdown_chunker import MarkdownChunker
from lumora_api.infrastructure.chunking.python_chunker import PythonChunker
from lumora_api.infrastructure.chunking.yaml_chunker import YamlChunker

_python_chunker = PythonChunker()
_javascript_chunker = JsTsChunker("javascript")  # also handles .jsx (JSX is native to this grammar)
_typescript_chunker = JsTsChunker("typescript")
_tsx_chunker = JsTsChunker("tsx")  # tree-sitter-typescript needs the separate "tsx" grammar for JSX
_markdown_chunker = MarkdownChunker()
_json_chunker = JsonChunker()
_yaml_chunker = YamlChunker()
_fallback_chunker = FixedSizeChunker()


def _select_chunker(language: str, path: str) -> Chunker | None:
    if language == "python":
        return _python_chunker
    if language == "javascript":
        return _javascript_chunker
    if language == "typescript":
        return _tsx_chunker if path.endswith(".tsx") else _typescript_chunker
    if language == "markdown":
        return _markdown_chunker
    if language == "json":
        return _json_chunker
    if language == "yaml":
        return _yaml_chunker
    return None


def chunk_file(language: str, path: str, content: str) -> list[ChunkSpan]:
    if not content.strip():
        return []

    chunker = _select_chunker(language, path)
    spans = chunker.chunk(content) if chunker is not None else []

    if not spans:
        # No parser for this language, or the parser found nothing
        # structural to split on — fall back rather than skip the file.
        spans = _fallback_chunker.chunk(content)

    return spans
