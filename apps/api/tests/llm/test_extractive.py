from lumora_api.domain.retrieval import RetrievedChunk
from lumora_api.infrastructure.llm.extractive import ExtractiveChatProvider


def _chunk(**overrides) -> RetrievedChunk:
    defaults = {
        "chunk_id": "abc",
        "file_path": "app.py",
        "language": "python",
        "symbol": "greet",
        "kind": "function",
        "start_line": 1,
        "end_line": 3,
        "content": "def greet(): ...",
        "score": 0.9,
    }
    return RetrievedChunk(**{**defaults, **overrides})


async def test_no_chunks_returns_explicit_no_results_message():
    provider = ExtractiveChatProvider()
    answer = await provider.generate_answer("what does greet do?", [])
    assert "No relevant code" in answer


async def test_answer_cites_file_path_and_line_range():
    provider = ExtractiveChatProvider()
    answer = await provider.generate_answer("what does greet do?", [_chunk()])
    assert "app.py:1-3" in answer
    assert "greet" in answer


async def test_answer_lists_every_chunk():
    chunks = [_chunk(symbol="a", file_path="a.py"), _chunk(symbol="b", file_path="b.py")]
    provider = ExtractiveChatProvider()
    answer = await provider.generate_answer("q", chunks)
    assert "a.py" in answer
    assert "b.py" in answer
