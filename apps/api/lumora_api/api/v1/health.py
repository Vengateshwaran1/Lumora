"""Liveness/readiness endpoint.

Checks process liveness only. Dependency readiness (Postgres, Redis,
Qdrant) is handled by Docker Compose healthchecks, not this endpoint —
keeping it dependency-free means it stays fast and reliable as a k8s/ECS
liveness probe once deployed (see docs/architecture/ARCHITECTURE.md §12).
"""

from fastapi import APIRouter
from pydantic import BaseModel

from lumora_api.core.container import SettingsDep

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    environment: str


@router.get("/health", response_model=HealthResponse)
async def get_health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.environment)
