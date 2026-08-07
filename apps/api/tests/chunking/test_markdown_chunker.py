from lumora_api.infrastructure.chunking.markdown_chunker import MarkdownChunker

SOURCE = """# Title

Intro text.

## Section A

Content A.

## Section B

Content B.
"""


def test_markdown_chunker_splits_on_headings():
    spans = MarkdownChunker().chunk(SOURCE)
    symbols = [s.symbol for s in spans]
    assert symbols == ["Title", "Section A", "Section B"]
    assert all(s.kind == "section" for s in spans)


def test_markdown_chunker_preamble_before_first_heading():
    source = "Some preamble text.\n\n# Title\n\nBody.\n"
    spans = MarkdownChunker().chunk(source)
    assert spans[0].symbol is None
    assert "preamble" in spans[0].content
    assert spans[1].symbol == "Title"


def test_markdown_chunker_no_headings_returns_single_section():
    source = "Just a paragraph, no headings at all.\n"
    spans = MarkdownChunker().chunk(source)
    assert len(spans) == 1
    assert spans[0].symbol is None


def test_markdown_chunker_empty_source_yields_no_chunks():
    assert MarkdownChunker().chunk("") == []
    assert MarkdownChunker().chunk("   \n  \n") == []
