from lumora_api.infrastructure.chunking.json_chunker import JsonChunker

SOURCE = """{
  "name": "lumora",
  "version": "0.1.0",
  "scripts": {
    "dev": "vite"
  }
}
"""


def test_json_chunker_splits_top_level_keys():
    spans = JsonChunker().chunk(SOURCE)
    symbols = [s.symbol for s in spans]
    assert symbols == ["name", "version", "scripts"]
    assert all(s.kind == "key" for s in spans)


def test_json_chunker_array_falls_back_to_whole_file():
    spans = JsonChunker().chunk('["a", "b", "c"]')
    assert len(spans) == 1
    assert spans[0].kind == "file"


def test_json_chunker_invalid_json_yields_no_chunks():
    assert JsonChunker().chunk("{not valid json") == []


def test_json_chunker_empty_source_yields_no_chunks():
    assert JsonChunker().chunk("") == []
