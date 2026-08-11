import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
from git import Repo
from httpx import ASGITransport, AsyncClient
from qdrant_client import AsyncQdrantClient

from lumora_api.core.config import get_settings
from lumora_api.infrastructure.database import get_session_factory
from lumora_api.infrastructure.embeddings.deterministic import DeterministicEmbeddingProvider
from lumora_api.infrastructure.vcs.git_service import GitService
from lumora_api.infrastructure.vector_store.qdrant_store import QdrantVectorStore
from lumora_api.main import create_app

TEST_EMBEDDING_DIMENSIONS = 32


@pytest.fixture
def app():
    """The FastAPI instance backing `client` — a separate fixture so tests
    can set `app.dependency_overrides` (e.g. swapping `get_job_queue` for
    `tests.fakes.FakeJobQueue`) before requests are made. Note `client`'s
    `ASGITransport` never runs the app's lifespan, so `app.state.arq_redis`
    is never set in tests — any dependency chain reaching it must be
    overridden rather than exercised live (see application/jobs/queue.py's
    docstring for why)."""
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


@pytest.fixture
def sample_repo_path(tmp_path: Path) -> str:
    """A small local git repo covering every Milestone 1 supported
    language, plus a build directory (should be excluded via `git
    ls-files`, same as `.gitignore` would in a real repo)."""
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir, initial_branch="main")
    repo.config_writer().set_value("user", "name", "Test").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    (repo_dir / "app.py").write_text(
        "class Greeter:\n"
        "    def greet(self, name: str) -> str:\n"
        '        return f"Hello, {name}"\n'
        "\n\n"
        "def add(a, b):\n"
        "    return a + b\n"
    )
    (repo_dir / "greeter.ts").write_text(
        "export function greet(name: string): string {\n  return `Hello, ${name}`;\n}\n"
    )
    (repo_dir / "README.md").write_text("# Sample\n\n## Usage\n\nCall `greet(name)`.\n")
    (repo_dir / "config.json").write_text('{\n  "name": "sample",\n  "version": "1.0.0"\n}\n')
    (repo_dir / "config.yaml").write_text("name: sample\nversion: '1.0.0'\n")

    (repo_dir / ".gitignore").write_text("build/\n")
    build_dir = repo_dir / "build"
    build_dir.mkdir()
    (build_dir / "output.py").write_text("# should never be indexed\n")

    repo.git.add(A=True)
    repo.index.commit("initial commit")
    return str(repo_dir)


@pytest.fixture
def git_service(tmp_path: Path) -> GitService:
    return GitService(tmp_path / "clones")


@dataclass
class RepoWithHistory:
    path: str
    commit_a: str  # initial commit — HEAD at fixture setup time
    push_commit_b: Callable[[], str]  # call after the baseline index to advance the repo


@pytest.fixture
def sample_repo_with_history(tmp_path: Path) -> RepoWithHistory:
    """Local git repo for incremental-indexing tests, exposing `commit_a`
    as HEAD immediately (so a baseline `index_repository` run — which
    clones whatever HEAD currently is — genuinely indexes commit A, not a
    later one) and `push_commit_b()` to advance the repo afterward,
    mirroring the real chronology a webhook fires against: index at A,
    *then* a push happens, moving HEAD to B. `push_commit_b()` modifies one
    file, adds one, deletes one, and renames one (unchanged content) —
    covering every diff status `incremental_index_repository` handles."""
    repo_dir = tmp_path / "history_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir, initial_branch="main")
    repo.config_writer().set_value("user", "name", "Test").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    (repo_dir / "app.py").write_text(
        "def add(a, b):\n    return a + b\n\n\ndef sub(a, b):\n    return a - b\n"
    )
    (repo_dir / "greeter.ts").write_text(
        "export function greet(name: string): string {\n  return `Hello, ${name}`;\n}\n"
    )
    (repo_dir / "doomed.py").write_text("def doomed():\n    return 'will be deleted'\n")
    repo.git.add(A=True)
    commit_a = repo.index.commit("commit A").hexsha

    def push_commit_b() -> str:
        (repo_dir / "app.py").write_text(
            "def add(a, b):\n    return a + b\n\n\ndef mul(a, b):\n    return a * b\n"
        )
        (repo_dir / "new_file.py").write_text("def new_thing():\n    return 42\n")
        (repo_dir / "doomed.py").unlink()
        repo.git.mv("greeter.ts", "renamed_greeter.ts")
        repo.git.add(A=True)
        return repo.index.commit("commit B").hexsha

    return RepoWithHistory(path=str(repo_dir), commit_a=commit_a, push_commit_b=push_commit_b)


@pytest.fixture
def deterministic_embedding_provider() -> DeterministicEmbeddingProvider:
    return DeterministicEmbeddingProvider(dimensions=TEST_EMBEDDING_DIMENSIONS)


@pytest.fixture
async def vector_store():
    """A throwaway Qdrant collection, deleted after the test — tests never
    share the app's real collection with each other or with dev data."""
    settings = get_settings()
    collection_name = f"test_{uuid.uuid4().hex}"
    store = QdrantVectorStore(settings.qdrant_url, collection_name)
    yield store
    client = AsyncQdrantClient(url=settings.qdrant_url, check_compatibility=False)
    if await client.collection_exists(collection_name):
        await client.delete_collection(collection_name)
