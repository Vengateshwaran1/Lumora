"""Milestone 3 §25 evaluation harness for the Planning Agent.

Not a CI gate — LLM-quality regression testing against a moving local
model isn't a green/red signal (see docs/architecture/milestone-3-planning-
agent.md's "Evaluation" section). Run manually to sanity-check citation
correctness, affected-file accuracy, and hallucination rate before
enabling `PLANNING_PROVIDER=ollama` for real use:

    uv run python -m tests.eval.planning_eval

Reads provider config from the normal `.env`/Settings — with the default
`PLANNING_PROVIDER=template` the affected-files/citations numbers are
trivially zero (the template provider never proposes either, by design),
so this is mostly a harness smoke test until `PLANNING_PROVIDER=ollama`
is set. Builds its own throwaway repo, Postgres rows, and Qdrant
collection; deletes all three when done.
"""

import asyncio
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from git import Repo
from langgraph.checkpoint.memory import InMemorySaver
from qdrant_client import AsyncQdrantClient

from lumora_api.agents.planning.graph import PlanningDeps, build_planning_graph
from lumora_api.application.indexing.index_repository import index_repository
from lumora_api.core.config import get_settings
from lumora_api.core.container import get_embedding_provider, get_planning_provider, get_reranker
from lumora_api.infrastructure.database import get_session_factory
from lumora_api.infrastructure.models import Issue, Repository, Run, RunType
from lumora_api.infrastructure.vcs.git_service import GitService
from lumora_api.infrastructure.vector_store.qdrant_store import QdrantVectorStore

MAX_FILE_SIZE = 1_000_000


@dataclass
class EvalCase:
    kind: str  # "feature" | "bugfix" | "refactor"
    title: str
    body: str
    expected_affected_files: set[str]


CASES = [
    EvalCase(
        kind="feature",
        title="Add a subtract endpoint",
        body=(
            "We already have `add(a, b)` in app.py. Add a `subtract(a, b)` "
            "function right next to it, following the same style."
        ),
        expected_affected_files={"app.py"},
    ),
    EvalCase(
        kind="bugfix",
        title="Greeting has no trailing punctuation",
        body=(
            "Greeter.greet() in app.py returns 'Hello, {name}' with no "
            "punctuation at the end. It should end with a period."
        ),
        expected_affected_files={"app.py"},
    ),
    EvalCase(
        kind="refactor",
        title="Unify greet() behavior across languages",
        body=(
            "Python's Greeter.greet() (app.py) and TypeScript's greet() "
            "(greeter.ts) should produce the exact same greeting format — "
            "align them."
        ),
        expected_affected_files={"app.py", "greeter.ts"},
    ),
]


@dataclass
class CaseResult:
    case: EvalCase
    predicted_affected_files: set[str]
    citations_valid: bool
    validation_errors: list[str]
    confidence: float


def _build_sample_repo(repo_dir: Path) -> None:
    repo_dir.mkdir(parents=True)
    repo = Repo.init(repo_dir, initial_branch="main")
    repo.config_writer().set_value("user", "name", "Eval").release()
    repo.config_writer().set_value("user", "email", "eval@example.com").release()

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

    repo.git.add(A=True)
    repo.index.commit("initial commit")


async def _run_case(deps: PlanningDeps, session, repository_id: uuid.UUID, case: EvalCase) -> CaseResult:
    issue = Issue(
        repository_id=repository_id,
        github_issue_id=abs(hash(case.title)) % 1_000_000,
        number=1,
        title=case.title,
        body=case.body,
        state="open",
        html_url="https://github.com/eval/eval/issues/1",
        labels=[case.kind],
    )
    session.add(issue)
    await session.commit()
    await session.refresh(issue)

    run = Run(repository_id=repository_id, issue_id=issue.id, run_type=RunType.PLANNING)
    session.add(run)
    await session.flush()
    run.langgraph_thread_id = str(run.id)
    await session.commit()
    await session.refresh(run)

    checkpointer = InMemorySaver()
    graph = build_planning_graph(deps, checkpointer)
    config = {"configurable": {"thread_id": str(run.id)}}
    result = await graph.ainvoke(
        {"run_id": str(run.id), "repository_id": str(repository_id), "issue_id": str(issue.id)},
        config=config,
    )

    plan = result["implementation_plan"] or {}
    predicted = set(plan.get("affected_files", []))
    retrieved_paths = {c["file_path"] for c in result["retrieved_chunks"]}
    citations = plan.get("citations", [])
    citations_valid = all(c["file_path"] in retrieved_paths for c in citations)

    return CaseResult(
        case=case,
        predicted_affected_files=predicted,
        citations_valid=citations_valid,
        validation_errors=result["validation_errors"],
        confidence=result["confidence"],
    )


def _print_report(results: list[CaseResult], provider_name: str) -> None:
    print(f"\nPlanning Agent eval — provider={provider_name}")
    print("=" * 60)
    if provider_name != "ollama":
        print(
            "NOTE: TemplatePlanningProvider never proposes affected_files/"
            "citations by design — precision/recall below are meaningless "
            "with this provider. Set PLANNING_PROVIDER=ollama to evaluate "
            "a real model.\n"
        )

    total_precision = 0.0
    total_recall = 0.0
    hallucinations = 0
    for r in results:
        expected = r.case.expected_affected_files
        predicted = r.predicted_affected_files
        true_positives = len(expected & predicted)
        precision = true_positives / len(predicted) if predicted else 0.0
        recall = true_positives / len(expected) if expected else 0.0
        total_precision += precision
        total_recall += recall
        if not r.citations_valid:
            hallucinations += 1

        print(f"[{r.case.kind}] {r.case.title}")
        print(f"  expected affected_files:  {sorted(expected)}")
        print(f"  predicted affected_files: {sorted(predicted)}")
        print(f"  precision={precision:.2f} recall={recall:.2f} confidence={r.confidence:.2f}")
        print(f"  citations_valid={r.citations_valid} validation_errors={r.validation_errors}")
        print()

    n = len(results)
    print("-" * 60)
    print(f"avg precision:                {total_precision / n:.2f}")
    print(f"avg recall:                   {total_recall / n:.2f}")
    print(f"citation hallucination rate:  {hallucinations}/{n}")


async def main() -> None:
    settings = get_settings()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_dir = tmp_path / "eval_repo"
        _build_sample_repo(repo_dir)

        git_service = GitService(tmp_path / "clones")
        embedding_provider = get_embedding_provider()
        planning_provider = get_planning_provider()
        reranker = get_reranker()

        collection_name = f"eval_{uuid.uuid4().hex}"
        vector_store = QdrantVectorStore(settings.qdrant_url, collection_name)

        session_factory = get_session_factory()
        async with session_factory() as session:
            repository = Repository(url=str(repo_dir), name="eval-repo")
            session.add(repository)
            await session.commit()
            await session.refresh(repository)

            await index_repository(
                repository_id=repository.id,
                session=session,
                git_service=git_service,
                embedding_provider=embedding_provider,
                vector_store=vector_store,
                max_file_size_bytes=MAX_FILE_SIZE,
            )

            deps = PlanningDeps(
                session=session,
                embedding_provider=embedding_provider,
                vector_store=vector_store,
                reranker=reranker,
                planning_provider=planning_provider,
                git_service=git_service,
            )

            results = [await _run_case(deps, session, repository.id, case) for case in CASES]

            # Cascades to the Issue/Run/IndexedFile/Chunk rows created above
            # — this is a repeatable manual tool, not a test with a
            # transactional rollback, so it cleans up after itself.
            await session.delete(repository)
            await session.commit()

        client = AsyncQdrantClient(url=settings.qdrant_url, check_compatibility=False)
        if await client.collection_exists(collection_name):
            await client.delete_collection(collection_name)

    _print_report(results, settings.planning_provider)


if __name__ == "__main__":
    asyncio.run(main())
