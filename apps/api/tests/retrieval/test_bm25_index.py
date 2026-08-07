from lumora_api.infrastructure.retrieval.bm25_index import Bm25Index


def test_search_ranks_exact_identifier_match_first():
    chunks = [
        ("1", "def calculate_total(items): return sum(items)"),
        ("2", "def unrelated_function(): pass"),
        ("3", "class Total: total = 0"),
    ]
    index = Bm25Index.build(chunks)
    results = index.search("calculate_total", limit=10)
    assert results[0] == "1"


def test_search_returns_empty_for_no_matches():
    index = Bm25Index.build([("1", "def foo(): pass")])
    assert index.search("zzz_nonexistent_term", limit=10) == []


def test_search_on_empty_corpus_returns_empty():
    index = Bm25Index.build([])
    assert index.search("anything", limit=10) == []


def test_search_respects_limit():
    chunks = [(str(i), f"def function_{i}(): pass") for i in range(10)]
    index = Bm25Index.build(chunks)
    results = index.search("function", limit=3)
    assert len(results) <= 3
