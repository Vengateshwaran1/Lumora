"""Shared AST-walking logic for tree-sitter-backed chunkers.

Subclasses implement `_classify`, which for a given node either declines
(returns None, base class recurses into its children looking for chunkable
nodes deeper in the tree) or claims it: returning the chunk's `kind`, the
node whose text is the symbol name, and which child nodes to keep
descending into (e.g. a class body, to also emit its methods as separate
chunks — the same span can legitimately produce more than one chunk).
"""

from tree_sitter import Node
from tree_sitter_language_pack import get_parser

from lumora_api.domain.chunk import ChunkSpan
from lumora_api.infrastructure.chunking.base import Chunker

ClassifyResult = tuple[str, Node | None, list[Node]] | None


class TreeSitterChunker(Chunker):
    def __init__(self, ts_language: str) -> None:
        self._parser = get_parser(ts_language)

    def chunk(self, content: str) -> list[ChunkSpan]:
        tree = self._parser.parse(content.encode("utf-8"))
        lines = content.splitlines()
        spans: list[ChunkSpan] = []
        self._walk(tree.root_node, ancestors=[], spans=spans, lines=lines)
        return spans

    def _walk(
        self, node: Node, ancestors: list[Node], spans: list[ChunkSpan], lines: list[str]
    ) -> None:
        result = self._classify(node, ancestors)
        if result is not None:
            kind, name_node, descend_into = result
            spans.append(self._make_span(node, kind, name_node, lines))
            for child in descend_into:
                self._walk(child, [*ancestors, node], spans, lines)
            return

        for child in node.children:
            self._walk(child, [*ancestors, node], spans, lines)

    def _make_span(
        self, node: Node, kind: str, name_node: Node | None, lines: list[str]
    ) -> ChunkSpan:
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        text = "\n".join(lines[start_line - 1 : end_line])
        symbol = name_node.text.decode("utf-8", "replace") if name_node and name_node.text else None
        return ChunkSpan(
            symbol=symbol, kind=kind, start_line=start_line, end_line=end_line, content=text
        )

    def _classify(self, node: Node, ancestors: list[Node]) -> ClassifyResult:
        raise NotImplementedError
