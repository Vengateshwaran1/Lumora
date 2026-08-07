from lumora_api.infrastructure.chunking.fallback import FixedSizeChunker
from lumora_api.infrastructure.chunking.registry import chunk_file


def test_fixed_size_chunker_splits_into_windows():
    content = "\n".join(f"line {i}" for i in range(150))
    chunker = FixedSizeChunker(lines_per_chunk=60)
    spans = chunker.chunk(content)

    assert len(spans) == 3  # 60, 60, 30
    assert all(s.kind == "block" and s.symbol is None for s in spans)
    assert spans[0].start_line == 1
    assert spans[0].end_line == 60
    assert spans[-1].end_line == 150


def test_fixed_size_chunker_empty_content_yields_no_chunks():
    assert FixedSizeChunker().chunk("") == []


def test_registry_falls_back_to_fixed_size_for_unsupported_language():
    content = "\n".join(f"line {i}" for i in range(10))
    spans = chunk_file("rust", "main.rs", content)
    assert spans  # fallback still produces something, not silently dropped
    assert spans[0].kind == "block"


def test_registry_falls_back_when_structural_chunker_finds_nothing():
    # valid Python with no top-level class/function declarations
    spans = chunk_file("python", "constants.py", "X = 1\nY = 2\n")
    assert spans
    assert spans[0].kind == "block"


def test_registry_uses_structural_chunker_when_available():
    spans = chunk_file("python", "app.py", "def f():\n    pass\n")
    assert spans[0].kind == "function"


def test_registry_empty_content_yields_no_chunks():
    assert chunk_file("python", "empty.py", "") == []


def test_registry_selects_tsx_grammar_for_tsx_extension():
    source = "export function C() {\n  return <div />;\n}\n"
    spans = chunk_file("typescript", "component.tsx", source)
    assert any(s.symbol == "C" for s in spans)
