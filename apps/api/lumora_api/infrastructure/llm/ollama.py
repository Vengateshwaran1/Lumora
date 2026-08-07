"""Answer generation via a local Ollama server's `/api/generate` endpoint.

`client` is injectable so unit tests can supply an `httpx.MockTransport`
instead of requiring a running Ollama instance.
"""

import httpx

from lumora_api.domain.retrieval import RetrievedChunk
from lumora_api.infrastructure.llm.base import ChatProvider

_SYSTEM_PROMPT = (
    "You are a code assistant. Answer the question using only the provided "
    "code context. Cite the file path and line numbers for every claim. "
    "If the context doesn't contain the answer, say so explicitly."
)


class OllamaChatProvider(ChatProvider):
    def __init__(self, base_url: str, model: str, client: httpx.AsyncClient | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = client or httpx.AsyncClient(timeout=120.0)

    async def generate_answer(self, question: str, chunks: list[RetrievedChunk]) -> str:
        prompt = (
            f"{_SYSTEM_PROMPT}\n\n"
            f"Context:\n{self._format_context(chunks)}\n\n"
            f"Question: {question}\nAnswer:"
        )
        response = await self._client.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        return str(response.json()["response"])

    @staticmethod
    def _format_context(chunks: list[RetrievedChunk]) -> str:
        parts = []
        for chunk in chunks:
            label = chunk.symbol or chunk.kind
            parts.append(
                f"[{chunk.file_path}:{chunk.start_line}-{chunk.end_line}] {label}\n{chunk.content}"
            )
        return "\n\n".join(parts)
