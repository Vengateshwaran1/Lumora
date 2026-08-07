"""Infrastructure layer: concrete adapters for external systems.

Postgres/Qdrant clients, the GitHub App client, and LLM provider clients
implement ports defined in `domain` / `application`. Only database
connection wiring exists in Milestone 0 — no ORM models or repositories yet.
"""
