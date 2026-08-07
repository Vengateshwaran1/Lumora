"""No live Ollama server is used or required — see tests/embeddings/test_ollama.py."""

import json

import httpx

from lumora_api.domain.retrieval import RetrievedChunk
from lumora_api.infrastructure.llm.ollama import OllamaChatProvider

_CHUNK = RetrievedChunk(
    chunk_id="abc",
    file_path="app.py",
    language="python",
    symbol="greet",
    kind="function",
    start_line=1,
    end_line=3,
    content="def greet(): ...",
    score=0.9,
)


async def test_generate_answer_calls_ollama_generate_endpoint():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"response": "Greet says hello."})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OllamaChatProvider("http://localhost:11434", "qwen3", client=client)

    answer = await provider.generate_answer("what does greet do?", [_CHUNK])

    assert answer == "Greet says hello."
    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["body"]["model"] == "qwen3"
    assert captured["body"]["stream"] is False
    assert "app.py:1-3" in captured["body"]["prompt"]
    assert "what does greet do?" in captured["body"]["prompt"]
