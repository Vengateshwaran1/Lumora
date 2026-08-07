"""Aggregates all v1 routers under a single APIRouter.

New feature routers (repos, chat, runs, ...) register here as they land —
`main.py` only ever mounts this one router under the versioned prefix.
"""

from fastapi import APIRouter

from lumora_api.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router)
