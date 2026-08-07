"""Use case: hybrid retrieval over one repository's indexed chunks.

Dense candidates come from Qdrant; BM25 candidates come from an index built
fresh over the repository's chunk corpus (see `Bm25Index` for why that's
fine at Milestone 1 scale). The two ranked lists are fused with Reciprocal
Rank Fusion — not a weighted score sum, since dense cosine similarity and
BM25 scores aren't on a comparable scale — then handed to the reranker
(a no-op by default; see `docs/architecture/ARCHITECTURE.md §5`).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.domain.retrieval import RetrievedChunk
from lumora_api.infrastructure.embeddings.base import EmbeddingProvider
from lumora_api.infrastructure.models import Chunk
from lumora_api.infrastructure.retrieval.bm25_index import Bm25Index
from lumora_api.infrastructure.retrieval.fusion import reciprocal_rank_fusion
from lumora_api.infrastructure.retrieval.reranker.base import Reranker
from lumora_api.infrastructure.vector_store.qdrant_store import QdrantVectorStore

_DENSE_CANDIDATES = 20
_BM25_CANDIDATES = 20


async def search_repository(
    *,
    repository_id: uuid.UUID,
    query: str,
    top_k: int,
    session: AsyncSession,
    embedding_provider: EmbeddingProvider,
    vector_store: QdrantVectorStore,
    reranker: Reranker,
) -> list[RetrievedChunk]:
    result = await session.execute(select(Chunk).where(Chunk.repository_id == repository_id))
    chunks_by_id = {str(chunk.id): chunk for chunk in result.scalars().all()}
    if not chunks_by_id:
        return []

    [query_vector] = await embedding_provider.embed([query])
    dense_hits = await vector_store.search(
        query_vector, str(repository_id), limit=_DENSE_CANDIDATES
    )
    dense_ranked_ids = [hit.point_id for hit in dense_hits]
    dense_scores = {hit.point_id: hit.score for hit in dense_hits}

    bm25_index = Bm25Index.build([(cid, chunk.content) for cid, chunk in chunks_by_id.items()])
    bm25_ranked_ids = bm25_index.search(query, limit=_BM25_CANDIDATES)

    fused = reciprocal_rank_fusion(dense_ranked_ids, bm25_ranked_ids)
    if not fused:
        return []

    ranked_ids = sorted(fused, key=lambda cid: fused[cid], reverse=True)

    candidates: list[RetrievedChunk] = []
    for chunk_id in ranked_ids:
        chunk = chunks_by_id.get(chunk_id)
        if chunk is None:
            continue  # present in Qdrant but not Postgres — skip defensively
        candidates.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                file_path=chunk.file_path,
                language=chunk.language,
                symbol=chunk.symbol,
                kind=chunk.kind,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                content=chunk.content,
                score=dense_scores.get(chunk_id, fused[chunk_id]),
            )
        )

    reranked = await reranker.rerank(query, candidates)
    return reranked[:top_k]
