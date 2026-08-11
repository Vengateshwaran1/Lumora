"""Naive-UTC timestamp helper shared by indexing use cases.

Naive, not `datetime.now(UTC)` directly — matches the schema's `TIMESTAMP
WITHOUT TIME ZONE` columns (`server_default=func.now()`); a tz-aware value
fails asyncpg's bind-parameter check against that column type.
"""

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
