"""No live Ollama server used or required — same `httpx.MockTransport`
pattern as tests/llm/test_ollama.py."""

import json

import httpx
import pytest

from lumora_api.agents.planning.schemas import SearchQueries
from lumora_api.infrastructure.llm.ollama_planning import OllamaPlanningProvider
from lumora_api.infrastructure.llm.planning import PlanGenerationError


async def test_generate_structured_returns_validated_model_on_first_success():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["model"] == "qwen3"
        assert body["format"] == SearchQueries.model_json_schema()
        return httpx.Response(200, json={"response": json.dumps({"queries": ["auth middleware"]})})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OllamaPlanningProvider("http://localhost:11434", "qwen3", client=client)

    result = await provider.generate_structured(prompt="find auth code", schema=SearchQueries)

    assert result.queries == ["auth middleware"]


async def test_generate_structured_retries_on_invalid_json_then_succeeds():
    responses = iter(
        [
            httpx.Response(200, json={"response": "not json at all"}),
            httpx.Response(200, json={"response": json.dumps({"queries": ["retry worked"]})}),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return next(responses)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OllamaPlanningProvider("http://localhost:11434", "qwen3", client=client)

    result = await provider.generate_structured(prompt="find auth code", schema=SearchQueries)

    assert result.queries == ["retry worked"]


async def test_generate_structured_raises_after_exhausting_retries():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "still not json"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OllamaPlanningProvider("http://localhost:11434", "qwen3", client=client)

    with pytest.raises(PlanGenerationError):
        await provider.generate_structured(prompt="find auth code", schema=SearchQueries)
