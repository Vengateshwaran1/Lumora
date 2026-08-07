from lumora_api.infrastructure.chunking.yaml_chunker import YamlChunker

SOURCE = """name: lumora
services:
  api:
    image: test
  web:
    image: test2
version: '1.0'
"""


def test_yaml_chunker_splits_top_level_keys_only():
    spans = YamlChunker().chunk(SOURCE)
    symbols = [s.symbol for s in spans]
    assert symbols == ["name", "services", "version"]
    assert all(s.kind == "key" for s in spans)


def test_yaml_chunker_does_not_split_on_nested_keys_with_same_name():
    # "image" appears twice, nested — must not be picked up as a top-level key.
    spans = YamlChunker().chunk(SOURCE)
    assert "image" not in [s.symbol for s in spans]


def test_yaml_chunker_non_mapping_falls_back_to_whole_file():
    spans = YamlChunker().chunk("- a\n- b\n- c\n")
    assert len(spans) == 1
    assert spans[0].kind == "file"


def test_yaml_chunker_empty_source_yields_no_chunks():
    assert YamlChunker().chunk("") == []
