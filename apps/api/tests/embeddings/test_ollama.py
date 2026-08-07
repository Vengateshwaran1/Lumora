"""No live Ollama server is used or required — requests are intercepted
with an httpx.MockTransport, which also documents the exact request/response
shape this provider expects from Ollama's `/api/embed` endpoint."""

import json

import httpx
import pytest

from lumora_api.infrastructure.embeddings.ollama import OllamaEmbeddingProvider


async def test_embed_calls_ollama_embed_endpoint_and_parses_response():
    captured_request: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["url"] = str(request.url)
        captured_request["body"] = json.loads(request.content)
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OllamaEmbeddingProvider("http://localhost:11434", "nomic-embed-text", client=client)

    vectors = await provider.embed(["hello", "world"])

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    assert captured_request["url"] == "http://localhost:11434/api/embed"
    assert captured_request["body"] == {
        "model": "nomic-embed-text",
        "input": ["hello", "world"],
    }


async def test_embed_raises_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "model not found"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OllamaEmbeddingProvider("http://localhost:11434", "missing-model", client=client)

    with pytest.raises(httpx.HTTPStatusError):
        await provider.embed(["hello"])


async def test_empty_input_skips_the_request_entirely():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not be called for empty input")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OllamaEmbeddingProvider("http://localhost:11434", "nomic-embed-text", client=client)

    assert await provider.embed([]) == []
