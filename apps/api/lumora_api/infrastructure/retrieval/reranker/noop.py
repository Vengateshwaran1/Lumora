"""Default reranker — no download, no extra latency. Keeps the fused
dense+BM25 ranking as-is. See cross_encoder.py for a real reranking
implementation, opt-in via settings.reranker_provider = "cross_encoder".
"""

from lumora_api.domain.retrieval import RetrievedChunk
from lumora_api.infrastructure.retrieval.reranker.base import Reranker


class NoOpReranker(Reranker):
    async def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        return chunks
