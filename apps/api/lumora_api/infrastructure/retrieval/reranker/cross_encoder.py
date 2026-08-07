"""Cross-encoder reranking via sentence-transformers.

Downloads model weights from Hugging Face on first use — that's why this
is opt-in (`settings.reranker_provider = "cross_encoder"`), not the
default: the project's "works completely offline except GitHub access"
constraint means nothing should silently reach the network. The
sentence_transformers import is deferred into `__init__` rather than
module scope so merely importing this module (or the package it lives in)
doesn't pull torch into every process — only actually constructing this
class does.
"""

import asyncio
from dataclasses import replace

from lumora_api.domain.retrieval import RetrievedChunk
from lumora_api.infrastructure.retrieval.reranker.base import Reranker


class CrossEncoderReranker(Reranker):
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(model_name)

    async def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not chunks:
            return chunks
        pairs = [(query, chunk.content) for chunk in chunks]
        scores = await asyncio.to_thread(self._model.predict, pairs)
        rescored = [
            replace(chunk, score=float(score)) for chunk, score in zip(chunks, scores, strict=True)
        ]
        return sorted(rescored, key=lambda chunk: chunk.score, reverse=True)
