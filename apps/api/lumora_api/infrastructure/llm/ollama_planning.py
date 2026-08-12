"""Structured-output `PlanningProvider` via a local Ollama server, using
its JSON-schema-constrained generation mode (`format=<schema>`) — Qwen (the
project's default `ollama_chat_model`) supports this. Falls back to a
retry loop with the validation error fed back into the prompt when a
model produces schema-invalid JSON despite the constraint, per Milestone
3 §21: "implement validation/retry/fallback behavior rather than silently
accepting malformed output."
"""

import json
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from lumora_api.infrastructure.llm.planning import PlanGenerationError, PlanningProvider

T = TypeVar("T", bound=BaseModel)

_MAX_ATTEMPTS = 3


class OllamaPlanningProvider(PlanningProvider):
    def __init__(self, base_url: str, model: str, client: httpx.AsyncClient | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = client or httpx.AsyncClient(timeout=180.0)

    async def generate_structured(self, *, prompt: str, schema: type[T]) -> T:
        current_prompt = prompt
        last_error: Exception | None = None

        for _attempt in range(1, _MAX_ATTEMPTS + 1):
            response = await self._client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": current_prompt,
                    "stream": False,
                    "format": schema.model_json_schema(),
                },
            )
            response.raise_for_status()
            raw_text = str(response.json()["response"])

            try:
                payload = json.loads(raw_text)
                return schema.model_validate(payload)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                current_prompt = (
                    f"{prompt}\n\nYour previous response was invalid: {exc}\n"
                    f"Previous response: {raw_text}\n"
                    "Return ONLY valid JSON matching the required schema, no other text."
                )

        raise PlanGenerationError(
            f"{schema.__name__} generation failed after {_MAX_ATTEMPTS} attempts: {last_error}"
        )
