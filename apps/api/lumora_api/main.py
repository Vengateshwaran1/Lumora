"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from arq.connections import RedisSettings, create_pool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lumora_api.api.v1.router import api_router
from lumora_api.api.webhooks import webhook_router
from lumora_api.core.config import get_settings
from lumora_api.core.container import build_checkpointer
from lumora_api.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    app.state.arq_redis = await create_pool(
        RedisSettings(
            host=settings.redis_host, port=settings.redis_port, database=settings.redis_db
        )
    )
    checkpointer_pool, app.state.checkpointer = await build_checkpointer()
    try:
        yield
    finally:
        await app.state.arq_redis.close()
        await checkpointer_pool.close()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Lumora API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    # Not under /api/v1 — GitHub calls this path directly, ARCHITECTURE.md §10.
    app.include_router(webhook_router)

    return app


app = create_app()
