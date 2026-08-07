"""Chunker for JavaScript, TypeScript, and TSX — one grammar family sharing
the same node types for everything Milestone 1 needs (class/function/method/
interface declarations, plus `const x = (...) => ...` arrow functions)."""

from tree_sitter import Node

from lumora_api.infrastructure.chunking.tree_sitter_base import ClassifyResult, TreeSitterChunker

_ARROW_VALUE_TYPES = frozenset({"arrow_function", "function_expression", "function"})


class JsTsChunker(TreeSitterChunker):
    def __init__(self, ts_language: str) -> None:
        super().__init__(ts_language)

    def _classify(self, node: Node, ancestors: list[Node]) -> ClassifyResult:
        if node.type == "export_statement":
            # `export` wraps the real declaration in a `declaration` field.
            # Classify the inner node but keep using the *outer* node's
            # span (the caller does this via `node`, not the inner one) so
            # the `export` keyword stays part of the chunk.
            inner = node.child_by_field_name("declaration")
            if inner is None:
                return None
            return self._classify(inner, ancestors)

        if node.type == "class_declaration":
            name = node.child_by_field_name("name")
            body = node.child_by_field_name("body")
            descend = list(body.children) if body is not None else []
            return "class", name, descend

        if node.type == "interface_declaration":
            name = node.child_by_field_name("name")
            return "interface", name, []

        if node.type == "function_declaration":
            name = node.child_by_field_name("name")
            return "function", name, []

        if node.type == "method_definition":
            name = node.child_by_field_name("name")
            return "method", name, []

        if node.type in ("lexical_declaration", "variable_declaration"):
            for declarator in node.children:
                if declarator.type != "variable_declarator":
                    continue
                value = declarator.child_by_field_name("value")
                if value is not None and value.type in _ARROW_VALUE_TYPES:
                    name = declarator.child_by_field_name("name")
                    return "function", name, []
            return None

        return None
