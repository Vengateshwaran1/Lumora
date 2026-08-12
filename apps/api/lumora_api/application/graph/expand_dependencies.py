"""Use case: given a set of already-retrieved chunk ids, pull their
directly-connected neighbors from the heuristic `symbol_edges` graph
(Milestone 3 §10's "Expand Code Graph" planning-graph node).

Returns `RetrievedChunk`s (score 0.0 — these aren't ranked by relevance,
they're included because they're graph-adjacent to something that was) so
the planning agent's context assembly can treat them uniformly with
directly-retrieved chunks, while still being able to tell them apart via
`related_symbols` in the planner state (agents/planning/state.py) if the
distinction matters downstream.
"""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.domain.retrieval import RetrievedChunk
from lumora_api.infrastructure.models import Chunk, SymbolEdge

_DEFAULT_MAX_NEIGHBORS = 20


async def expand_dependencies(
    *,
    repository_id: uuid.UUID,
    chunk_ids: list[str],
    session: AsyncSession,
    max_neighbors: int = _DEFAULT_MAX_NEIGHBORS,
) -> list[RetrievedChunk]:
    if not chunk_ids:
        return []

    seed_ids = {uuid.UUID(cid) for cid in chunk_ids}

    edges_result = await session.execute(
        select(SymbolEdge.from_chunk_id, SymbolEdge.to_chunk_id).where(
            SymbolEdge.repository_id == repository_id,
            or_(SymbolEdge.from_chunk_id.in_(seed_ids), SymbolEdge.to_chunk_id.in_(seed_ids)),
        )
    )
    neighbor_ids: set[uuid.UUID] = set()
    for from_id, to_id in edges_result.all():
        if from_id in seed_ids and to_id not in seed_ids:
            neighbor_ids.add(to_id)
        elif to_id in seed_ids and from_id not in seed_ids:
            neighbor_ids.add(from_id)
        if len(neighbor_ids) >= max_neighbors:
            break

    if not neighbor_ids:
        return []

    chunks_result = await session.execute(select(Chunk).where(Chunk.id.in_(neighbor_ids)))
    return [
        RetrievedChunk(
            chunk_id=str(chunk.id),
            file_path=chunk.file_path,
            language=chunk.language,
            symbol=chunk.symbol,
            kind=chunk.kind,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            content=chunk.content,
            score=0.0,
        )
        for chunk in chunks_result.scalars().all()
    ]
