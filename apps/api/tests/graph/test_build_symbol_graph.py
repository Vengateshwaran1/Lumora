"""build_symbol_graph / expand_dependencies — heuristic reference/import
edges over already-chunked content, no Qdrant/embedding involved (see
infrastructure/models.py::SymbolEdge's docstring for why this is
name-reference matching, not an AST call graph)."""

import uuid

from sqlalchemy import select

from lumora_api.application.graph.build_symbol_graph import build_symbol_graph
from lumora_api.application.graph.expand_dependencies import expand_dependencies
from lumora_api.infrastructure.models import (
    Chunk,
    IndexedFile,
    Repository,
    SymbolEdge,
    SymbolEdgeType,
)


async def _seed_repo(db_session) -> tuple[Repository, dict[str, Chunk]]:
    repository = Repository(url="https://example.invalid/graph-test.git", name="graph-test")
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)

    controller_file = IndexedFile(
        repository_id=repository.id, path="controller.py", language="python", content_hash="a" * 64
    )
    service_file = IndexedFile(
        repository_id=repository.id, path="service.py", language="python", content_hash="b" * 64
    )
    db_session.add_all([controller_file, service_file])
    await db_session.commit()
    await db_session.refresh(controller_file)
    await db_session.refresh(service_file)

    chunks = {
        "import": Chunk(
            repository_id=repository.id,
            file_id=controller_file.id,
            file_path="controller.py",
            language="python",
            symbol=None,
            kind="import",
            start_line=1,
            end_line=1,
            content="from service import service_call",
            content_hash="c" * 64,
            qdrant_point_id=str(uuid.uuid4()),
        ),
        "handle_request": Chunk(
            repository_id=repository.id,
            file_id=controller_file.id,
            file_path="controller.py",
            language="python",
            symbol="handle_request",
            kind="function",
            start_line=3,
            end_line=6,
            content="def handle_request(req):\n    return service_call(req)\n",
            content_hash="d" * 64,
            qdrant_point_id=str(uuid.uuid4()),
        ),
        "service_call": Chunk(
            repository_id=repository.id,
            file_id=service_file.id,
            file_path="service.py",
            language="python",
            symbol="service_call",
            kind="function",
            start_line=1,
            end_line=2,
            content="def service_call(req):\n    return {'ok': True}\n",
            content_hash="e" * 64,
            qdrant_point_id=str(uuid.uuid4()),
        ),
    }
    db_session.add_all(chunks.values())
    await db_session.commit()
    for chunk in chunks.values():
        await db_session.refresh(chunk)

    return repository, chunks


async def test_build_symbol_graph_creates_reference_edge_for_call(db_session):
    repository, chunks = await _seed_repo(db_session)

    stats = await build_symbol_graph(repository_id=repository.id, session=db_session)

    assert stats.references_created >= 1
    result = await db_session.execute(
        select(SymbolEdge).where(
            SymbolEdge.repository_id == repository.id,
            SymbolEdge.from_chunk_id == chunks["handle_request"].id,
            SymbolEdge.to_chunk_id == chunks["service_call"].id,
            SymbolEdge.edge_type == SymbolEdgeType.REFERENCES,
        )
    )
    assert result.scalar_one_or_none() is not None


async def test_build_symbol_graph_creates_import_edge(db_session):
    repository, chunks = await _seed_repo(db_session)

    await build_symbol_graph(repository_id=repository.id, session=db_session)

    result = await db_session.execute(
        select(SymbolEdge).where(
            SymbolEdge.repository_id == repository.id,
            SymbolEdge.from_chunk_id == chunks["import"].id,
            SymbolEdge.to_chunk_id == chunks["service_call"].id,
            SymbolEdge.edge_type == SymbolEdgeType.IMPORTS,
        )
    )
    assert result.scalar_one_or_none() is not None


async def test_build_symbol_graph_sets_repository_timestamp(db_session):
    repository, _ = await _seed_repo(db_session)
    assert repository.symbol_graph_built_at is None

    await build_symbol_graph(repository_id=repository.id, session=db_session)
    await db_session.refresh(repository)

    assert repository.symbol_graph_built_at is not None


async def test_build_symbol_graph_is_idempotent(db_session):
    repository, _ = await _seed_repo(db_session)

    first = await build_symbol_graph(repository_id=repository.id, session=db_session)
    second = await build_symbol_graph(repository_id=repository.id, session=db_session)

    assert first.total_created == second.total_created
    result = await db_session.execute(
        select(SymbolEdge).where(SymbolEdge.repository_id == repository.id)
    )
    assert len(result.scalars().all()) == second.total_created


async def test_expand_dependencies_returns_graph_neighbors(db_session):
    repository, chunks = await _seed_repo(db_session)
    await build_symbol_graph(repository_id=repository.id, session=db_session)

    neighbors = await expand_dependencies(
        repository_id=repository.id,
        chunk_ids=[str(chunks["handle_request"].id)],
        session=db_session,
    )

    neighbor_ids = {n.chunk_id for n in neighbors}
    assert str(chunks["service_call"].id) in neighbor_ids


async def test_expand_dependencies_with_no_edges_returns_empty(db_session):
    repository = Repository(url="https://example.invalid/empty-graph.git", name="empty-graph")
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)

    neighbors = await expand_dependencies(
        repository_id=repository.id, chunk_ids=[str(uuid.uuid4())], session=db_session
    )
    assert neighbors == []
