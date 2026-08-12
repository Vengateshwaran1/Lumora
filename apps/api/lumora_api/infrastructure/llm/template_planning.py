"""Offline default `PlanningProvider` — no LLM call at all, same role
`ExtractiveChatProvider` plays for `/chat`. Keeps CI, the planning graph's
unit tests, and any environment without Ollama configured fully
functional, producing a low-confidence but schema-valid result instead of
failing outright.

Deliberately does *not* know about any specific schema (`IssueAnalysis`,
`ImplementationPlan`, ...) — that would put a business-logic dependency
into `infrastructure/`. Instead, each schema that needs an offline
fallback implements a classmethod `offline_default(prompt: str) -> Self`
(see `agents/planning/schemas.py`); this provider just calls it via duck
typing and raises `PlanGenerationError` for any schema that doesn't.
"""

from typing import TypeVar

from pydantic import BaseModel

from lumora_api.infrastructure.llm.planning import PlanGenerationError, PlanningProvider

T = TypeVar("T", bound=BaseModel)


class TemplatePlanningProvider(PlanningProvider):
    async def generate_structured(self, *, prompt: str, schema: type[T]) -> T:
        offline_default = getattr(schema, "offline_default", None)
        if offline_default is None:
            raise PlanGenerationError(
                f"{schema.__name__} has no offline_default(); TemplatePlanningProvider can't "
                "produce a fallback instance for it."
            )
        result: T = offline_default(prompt)
        return result
