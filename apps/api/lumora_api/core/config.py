"""Application configuration, sourced from environment variables / .env."""

from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, RedisDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API process.

    Values are read from environment variables (or a local `.env` file for
    host-run development). Docker Compose injects these directly as
    container environment variables using service-network hostnames.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173"]

    secret_key: str = "change_me_in_production"

    postgres_user: str = "lumora"
    postgres_password: str = "lumora_dev_password"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "lumora"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "lumora_chunks"

    # Local storage for cloned repositories. Compose mounts a named volume
    # here; host-run dev defaults to a repo-relative gitignored directory.
    repo_storage_path: str = "./.data/repos"

    # Cap on individual file size considered for chunking — guards against
    # accidentally parsing huge generated/data files that slipped past
    # `git ls-files` filtering.
    max_file_size_bytes: int = 1_000_000

    # "deterministic" (hash-seeded, no network, no weights) is the default
    # so `docker compose up` produces a working pipeline with zero setup.
    # Switch to "ollama" once Ollama is running and a model is pulled — see
    # README's Ollama setup section.
    embedding_provider: Literal["ollama", "deterministic"] = "deterministic"
    embedding_dimensions: int = 768  # only used by the deterministic provider

    # "extractive" needs no LLM at all (templates retrieved chunks into an
    # answer) so /chat works offline out of the box. "ollama" gives real
    # generated answers once Ollama + ollama_chat_model are available.
    chat_provider: Literal["ollama", "extractive"] = "extractive"

    # host.docker.internal resolves to the Docker host from inside a
    # container — Ollama runs on the host, not as a compose service.
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_chat_model: str = "qwen3"

    # Cross-encoder reranking downloads model weights from Hugging Face on
    # first use, which conflicts with "works completely offline" as a
    # default. Off by default; "cross_encoder" is an explicit opt-in once
    # weights have been fetched at least once.
    reranker_provider: Literal["none", "cross_encoder"] = "none"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        dsn = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_db,
        )
        return str(dsn)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        dsn = RedisDsn.build(
            scheme="redis",
            host=self.redis_host,
            port=self.redis_port,
            path=str(self.redis_db),
        )
        return str(dsn)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings provider — the single DI entry point for config."""
    return Settings()
