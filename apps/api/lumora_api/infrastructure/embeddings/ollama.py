"""Embeddings via a local Ollama server's batch `/api/embed` endpoint.

`client` is injectable so unit tests can supply an `httpx.MockTransport`
instead of requiring a running Ollama instance.
"""

import httpx

from lumora_api.infrastructure.embeddings.base import EmbeddingProvider


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, base_url: str, model: str, client: httpx.AsyncClient | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = client or httpx.AsyncClient(timeout=60.0)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self._client.post(
            f"{self._base_url}/api/embed",
            json={"model": self._model, "input": texts},
        )
        response.raise_for_status()
        data = response.json()
        return list(data["embeddings"])
