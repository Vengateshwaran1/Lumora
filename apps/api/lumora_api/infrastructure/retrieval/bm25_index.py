"""BM25 lexical retrieval over a repository's chunk corpus.

Dense embeddings capture semantic similarity but miss exact identifier or
error-string matches developers actually search for — BM25 covers that
gap (see docs/architecture/ARCHITECTURE.md §5). Built fresh per search
from the chunk rows already loaded for a repository — no separate
persisted index. That's fine at Milestone 1 scale (one repo, hundreds to
low-thousands of chunks, built in milliseconds); revisit with a
cached/persisted index if corpus size or query volume grows enough for
rebuild cost to matter.
"""

import re

from rank_bm25 import BM25Okapi

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class Bm25Index:
    def __init__(self, chunk_ids: list[str], bm25: BM25Okapi | None) -> None:
        self._chunk_ids = chunk_ids
        self._bm25 = bm25

    @classmethod
    def build(cls, chunks: list[tuple[str, str]]) -> "Bm25Index":
        """`chunks`: (chunk_id, content) pairs."""
        if not chunks:
            return cls([], None)
        chunk_ids = [chunk_id for chunk_id, _ in chunks]
        tokenized_corpus = [_tokenize(content) for _, content in chunks]
        return cls(chunk_ids, BM25Okapi(tokenized_corpus))

    def search(self, query: str, limit: int) -> list[str]:
        """Returns chunk_ids in rank order (best first); positive-score matches only."""
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(
            zip(self._chunk_ids, scores, strict=True), key=lambda pair: pair[1], reverse=True
        )
        return [chunk_id for chunk_id, score in ranked[:limit] if score > 0]
