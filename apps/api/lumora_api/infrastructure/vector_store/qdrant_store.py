"""Thin async wrapper around qdrant-client for the one collection this
project uses (see docs/architecture/ARCHITECTURE.md §8: one collection per
environment, filtered by `repository_id` payload — not one collection per
repo, which stops scaling once repo count reaches the thousands).
"""

from dataclasses import dataclass
from typing import Any

from qdrant_client import AsyncQdrantClient, models


@dataclass(frozen=True)
class VectorPoint:
    id: str
    vector: list[float]
    payload: dict[str, Any]


@dataclass(frozen=True)
class VectorHit:
    point_id: str
    score: float
    payload: dict[str, Any]


class QdrantVectorStore:
    def __init__(self, url: str, collection_name: str) -> None:
        # check_compatibility=False: qdrant-client's version is ahead of
        # the pinned qdrant/qdrant server image in docker-compose.yml — a
        # deliberate, tested pin, not an accidental mismatch.
        self._client = AsyncQdrantClient(url=url, check_compatibility=False)
        self._collection_name = collection_name
        self._ensured_dimensions: int | None = None

    async def ensure_collection(self, dimensions: int) -> None:
        """Idempotent, cheap to call on every indexing run — creates the
        collection on first use, sized to whatever the active embedding
        provider actually returns rather than a hardcoded constant."""
        if self._ensured_dimensions == dimensions:
            return
        exists = await self._client.collection_exists(self._collection_name)
        if not exists:
            await self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=models.VectorParams(
                    size=dimensions, distance=models.Distance.COSINE
                ),
            )
            await self._client.create_payload_index(
                collection_name=self._collection_name,
                field_name="repository_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        self._ensured_dimensions = dimensions

    async def upsert(self, points: list[VectorPoint]) -> None:
        if not points:
            return
        await self._client.upsert(
            collection_name=self._collection_name,
            points=[
                models.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points
            ],
        )

    async def delete(self, point_ids: list[str]) -> None:
        if not point_ids:
            return
        await self._client.delete(
            collection_name=self._collection_name,
            points_selector=models.PointIdsList(points=point_ids),
        )

    async def delete_by_repository(self, repository_id: str) -> None:
        await self._client.delete(
            collection_name=self._collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="repository_id", match=models.MatchValue(value=repository_id)
                        )
                    ]
                )
            ),
        )

    async def search(
        self, query_vector: list[float], repository_id: str, limit: int
    ) -> list[VectorHit]:
        result = await self._client.query_points(
            collection_name=self._collection_name,
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="repository_id", match=models.MatchValue(value=repository_id)
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
        )
        return [
            VectorHit(point_id=str(point.id), score=point.score, payload=point.payload or {})
            for point in result.points
        ]
