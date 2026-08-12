"""Port for the Planning Agent's structured-output LLM calls — parallel to
`ChatProvider` (Milestone 1), but returns a validated Pydantic model
instead of free text, since every call site (analyze_issue, generate
search queries, generate the implementation plan) needs a typed result,
not prose.
"""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class PlanGenerationError(Exception):
    """Raised when a structured-output call can't produce a schema-valid
    result after retrying — callers (agents.planning.graph) must not
    silently accept or fabricate a substitute; this should surface as a
    failed run with a clear error_message."""


class PlanningProvider(ABC):
    @abstractmethod
    async def generate_structured(self, *, prompt: str, schema: type[T]) -> T:
        """Generate a response conforming to `schema` from `prompt`.
        Implementations own their own retry policy for malformed output —
        see `OllamaPlanningProvider` — and must raise `PlanGenerationError`
        rather than return an invalid/partial instance."""
