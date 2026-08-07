"""Hash-seeded pseudo-random embeddings — no network call, no model weights.

Not semantically meaningful: unrelated texts get unrelated vectors, and
similar texts do *not* reliably land near each other, so this is not a
substitute for real embeddings in production use. Its purpose is to make
the full indexing → Qdrant → retrieval pipeline exercisable deterministically
and completely offline — in tests, in CI, and as the zero-config default so
`docker compose up` produces a working pipeline before Ollama is set up.
Same input text always produces the same vector, so re-indexing an
unchanged chunk is still a no-op. Switch to OllamaEmbeddingProvider for
real semantic search.
"""

import hashlib
import random

from lumora_api.infrastructure.embeddings.base import EmbeddingProvider


class DeterministicEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimensions: int) -> None:
        self._dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
        rng = random.Random(seed)
        vector = [rng.uniform(-1.0, 1.0) for _ in range(self._dimensions)]
        norm = sum(v * v for v in vector) ** 0.5
        if norm == 0:
            return vector
        return [v / norm for v in vector]
