import uuid
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
async def client():
    app = create_app()
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
