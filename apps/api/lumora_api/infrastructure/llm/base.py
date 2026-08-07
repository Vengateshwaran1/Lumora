from abc import ABC, abstractmethod

from lumora_api.domain.retrieval import RetrievedChunk


class ChatProvider(ABC):
    @abstractmethod
    async def generate_answer(self, question: str, chunks: list[RetrievedChunk]) -> str:
        """Generate an answer to `question`, grounded in `chunks`."""
