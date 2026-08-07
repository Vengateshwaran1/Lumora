from abc import ABC, abstractmethod

from lumora_api.domain.retrieval import RetrievedChunk


class Reranker(ABC):
    @abstractmethod
    async def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Return `chunks` reordered (and optionally rescored) by relevance to `query`."""
