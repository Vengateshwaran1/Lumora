from lumora_api.infrastructure.chunking.python_chunker import PythonChunker

SOURCE = '''class Foo:
    """Docstring."""

    def method_one(self, x: int) -> int:
        return x + 1

    async def method_two(self):
        pass


def standalone_function(a, b):
    return a + b
'''


def test_python_chunker_finds_class_methods_and_function():
    spans = PythonChunker().chunk(SOURCE)
    by_symbol = {s.symbol: s for s in spans}

    assert by_symbol["Foo"].kind == "class"
    assert by_symbol["method_one"].kind == "method"
    assert by_symbol["method_two"].kind == "method"
    assert by_symbol["standalone_function"].kind == "function"


def test_python_chunker_line_ranges_are_1_indexed_and_inclusive():
    spans = PythonChunker().chunk(SOURCE)
    method = next(s for s in spans if s.symbol == "method_one")

    lines = SOURCE.splitlines()
    assert lines[method.start_line - 1].strip().startswith("def method_one")
    assert "return x + 1" in lines[method.end_line - 1]


def test_python_chunker_empty_source_yields_no_chunks():
    assert PythonChunker().chunk("") == []


def test_python_chunker_source_with_no_declarations_yields_no_chunks():
    assert PythonChunker().chunk("x = 1\ny = 2\n") == []
