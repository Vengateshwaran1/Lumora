from tree_sitter import Node

from lumora_api.infrastructure.chunking.tree_sitter_base import ClassifyResult, TreeSitterChunker


class PythonChunker(TreeSitterChunker):
    def __init__(self) -> None:
        super().__init__("python")

    def _classify(self, node: Node, ancestors: list[Node]) -> ClassifyResult:
        if node.type == "class_definition":
            name = node.child_by_field_name("name")
            body = node.child_by_field_name("body")
            descend = list(body.children) if body is not None else []
            return "class", name, descend

        if node.type == "function_definition":
            in_class = any(a.type == "class_definition" for a in ancestors)
            name = node.child_by_field_name("name")
            return ("method" if in_class else "function"), name, []

        return None
