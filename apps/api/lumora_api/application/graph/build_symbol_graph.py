"""Use case: build the heuristic Postgres "symbol graph" for one repository
(Milestone 3 §10 — see `infrastructure.models.SymbolEdge`'s docstring for
why this is name-reference/import matching, not an AST-resolved call
graph).

Idempotent — a rebuild first deletes the repository's existing edges, so
calling this again after a reindex (or lazily from the planning graph)
never accumulates stale/duplicate edges.

**Algorithm, deliberately simple** (kept in-process over already-chunked
content, no new parsing pass, no new dependency):

- *references*: one alternation regex over every distinct symbol name in
  the repo, scanned once per chunk's content. A hit on `chunks.symbol`
  named `X` inside a chunk that doesn't itself define `X` becomes a
  `references` edge to every chunk that defines `X` (capped — a very
  common name like `get` can otherwise fan out to hundreds of chunks).
- *imports*: chunks with `kind == "import"` are matched against
  `indexed_files.path` by filename stem (e.g. an `import ... from "./foo"`
  matches a file whose stem is `foo`) — a simple, language-agnostic
  approximation, not per-language import-resolution logic.

Both are capped at `_MAX_NEIGHBORS_PER_EDGE_GROUP` to keep both the write
volume and later `expand_dependencies` traversals bounded.
"""

import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.core.time import utcnow
from lumora_api.infrastructure.models import (
    Chunk,
    IndexedFile,
    Repository,
    SymbolEdge,
    SymbolEdgeType,
)

_MAX_NEIGHBORS_PER_EDGE_GROUP = 25
_MIN_SYMBOL_NAME_LENGTH = 3  # skips noisy 1-2 char names ("i", "ok", "id" excepted by length only)


@dataclass
class SymbolGraphStats:
    chunks_scanned: int = 0
    references_created: int = 0
    imports_created: int = 0
    edges: list[tuple[uuid.UUID, uuid.UUID, SymbolEdgeType]] = field(default_factory=list)

    @property
    def total_created(self) -> int:
        return self.references_created + self.imports_created


async def build_symbol_graph(
    *, repository_id: uuid.UUID, session: AsyncSession
) -> SymbolGraphStats:
    chunks_result = await session.execute(
        select(Chunk).where(Chunk.repository_id == repository_id)
    )
    chunks = list(chunks_result.scalars().all())
    stats = SymbolGraphStats(chunks_scanned=len(chunks))

    await session.execute(delete(SymbolEdge).where(SymbolEdge.repository_id == repository_id))

    if not chunks:
        await session.commit()
        return stats

    symbol_to_chunk_ids: dict[str, list[uuid.UUID]] = defaultdict(list)
    for chunk in chunks:
        if chunk.symbol and len(chunk.symbol) >= _MIN_SYMBOL_NAME_LENGTH:
            symbol_to_chunk_ids[chunk.symbol].append(chunk.id)

    reference_pairs = _find_reference_edges(chunks, symbol_to_chunk_ids)
    for from_id, to_id in reference_pairs:
        session.add(
            SymbolEdge(
                repository_id=repository_id,
                from_chunk_id=from_id,
                to_chunk_id=to_id,
                edge_type=SymbolEdgeType.REFERENCES,
            )
        )
        stats.edges.append((from_id, to_id, SymbolEdgeType.REFERENCES))
    stats.references_created = len(reference_pairs)

    files_result = await session.execute(
        select(IndexedFile).where(IndexedFile.repository_id == repository_id)
    )
    files = list(files_result.scalars().all())
    import_pairs = _find_import_edges(chunks, files)
    for from_id, to_id in import_pairs:
        session.add(
            SymbolEdge(
                repository_id=repository_id,
                from_chunk_id=from_id,
                to_chunk_id=to_id,
                edge_type=SymbolEdgeType.IMPORTS,
            )
        )
        stats.edges.append((from_id, to_id, SymbolEdgeType.IMPORTS))
    stats.imports_created = len(import_pairs)

    repository = await session.get(Repository, repository_id)
    if repository is not None:
        repository.symbol_graph_built_at = utcnow()

    await session.commit()
    return stats


def _find_reference_edges(
    chunks: list[Chunk], symbol_to_chunk_ids: dict[str, list[uuid.UUID]]
) -> list[tuple[uuid.UUID, uuid.UUID]]:
    if not symbol_to_chunk_ids:
        return []

    # Longest-first avoids partial-name shadowing in the alternation.
    names = sorted(symbol_to_chunk_ids, key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(re.escape(name) for name in names) + r")\b")

    pairs: list[tuple[uuid.UUID, uuid.UUID]] = []
    for chunk in chunks:
        if not chunk.content:
            continue
        own_names = {chunk.symbol} if chunk.symbol else set()
        neighbor_ids: set[uuid.UUID] = set()
        for match in pattern.finditer(chunk.content):
            name = match.group(1)
            if name in own_names:
                continue
            for target_id in symbol_to_chunk_ids.get(name, ()):
                if target_id != chunk.id:
                    neighbor_ids.add(target_id)
            if len(neighbor_ids) >= _MAX_NEIGHBORS_PER_EDGE_GROUP:
                break
        pairs.extend((chunk.id, target_id) for target_id in neighbor_ids)
    return pairs


def _find_import_edges(
    chunks: list[Chunk], files: list[IndexedFile]
) -> list[tuple[uuid.UUID, uuid.UUID]]:
    import_chunks = [c for c in chunks if c.kind == "import" and c.content]
    if not import_chunks:
        return []

    chunks_by_file_id: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
    for chunk in chunks:
        chunks_by_file_id[chunk.file_id].append(chunk.id)

    stem_to_file_ids: dict[str, list[uuid.UUID]] = defaultdict(list)
    for file in files:
        stem = PurePosixPath(file.path).stem
        if stem and stem != "__init__":
            stem_to_file_ids[stem].append(file.id)

    module_token_pattern = re.compile(r"[\"']([^\"']+)[\"']|(?:from|import)\s+([\w.]+)")

    pairs: list[tuple[uuid.UUID, uuid.UUID]] = []
    for chunk in import_chunks:
        matched_file_ids: set[uuid.UUID] = set()
        for match in module_token_pattern.finditer(chunk.content):
            token = match.group(1) or match.group(2) or ""
            stem = PurePosixPath(token.replace(".", "/")).stem
            for file_id in stem_to_file_ids.get(stem, ()):
                matched_file_ids.add(file_id)
            if len(matched_file_ids) >= _MAX_NEIGHBORS_PER_EDGE_GROUP:
                break

        neighbor_ids: set[uuid.UUID] = set()
        for file_id in matched_file_ids:
            for target_id in chunks_by_file_id.get(file_id, ()):
                if target_id != chunk.id:
                    neighbor_ids.add(target_id)
        pairs.extend((chunk.id, target_id) for target_id in neighbor_ids)
    return pairs
