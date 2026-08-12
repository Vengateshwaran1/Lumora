"""Integration test for the Planning Agent's LangGraph graph (Milestone 3
§28's verification gate, at unit-test scope): a real indexed repository +
real retrieval + `TemplatePlanningProvider` (no Ollama needed, matching
`docs/architecture/milestone-*` conventions of CI never requiring a live
LLM) + an in-memory checkpointer (fast, no Postgres checkpoint tables
needed for this test) — exercises load_issue through the human_review
interrupt, then resumes it, same flow the API's approve endpoint drives.
"""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from lumora_api.agents.planning.graph import PlanningDeps, build_planning_graph
from lumora_api.application.indexing.index_repository import index_repository
from lumora_api.infrastructure.llm.template_planning import TemplatePlanningProvider
from lumora_api.infrastructure.models import Issue, Repository, Run, RunStatus, RunType
from lumora_api.infrastructure.retrieval.reranker.noop import NoOpReranker

MAX_FILE_SIZE = 1_000_000


async def _setup_run(
    db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
) -> Run:
    repository = Repository(url=sample_repo_path, name="sample")
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)

    await index_repository(
        repository_id=repository.id,
        session=db_session,
        git_service=git_service,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        max_file_size_bytes=MAX_FILE_SIZE,
    )

    issue = Issue(
        repository_id=repository.id,
        github_issue_id=1,
        number=1,
        title="Add a greeting API",
        body="Expose the existing greet() function over an HTTP endpoint.",
        state="open",
        html_url="https://github.com/o/r/issues/1",
        labels=[],
    )
    db_session.add(issue)
    await db_session.commit()
    await db_session.refresh(issue)

    run = Run(
        repository_id=repository.id,
        issue_id=issue.id,
        run_type=RunType.PLANNING,
        status=RunStatus.QUEUED,
    )
    db_session.add(run)
    await db_session.flush()
    run.langgraph_thread_id = str(run.id)
    await db_session.commit()
    await db_session.refresh(run)
    return run


def _initial_state(run: Run) -> dict:
    return {
        "run_id": str(run.id),
        "repository_id": str(run.repository_id),
        "issue_id": str(run.issue_id),
    }


def _deps(db_session, git_service, deterministic_embedding_provider, vector_store) -> PlanningDeps:
    return PlanningDeps(
        session=db_session,
        embedding_provider=deterministic_embedding_provider,
        vector_store=vector_store,
        reranker=NoOpReranker(),
        planning_provider=TemplatePlanningProvider(),
        git_service=git_service,
    )


async def test_graph_reaches_awaiting_approval_and_populates_plan(
    db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
):
    run = await _setup_run(
        db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
    )
    deps = _deps(db_session, git_service, deterministic_embedding_provider, vector_store)
    checkpointer = InMemorySaver()
    graph = build_planning_graph(deps, checkpointer)
    config = {"configurable": {"thread_id": str(run.id)}}

    await graph.ainvoke(_initial_state(run), config=config)

    await db_session.refresh(run)
    assert run.status == RunStatus.AWAITING_APPROVAL
    assert run.implementation_plan is not None
    # Template provider never fabricates citations.
    assert run.implementation_plan["citations"] == []

    state = await graph.aget_state(config)
    assert state.next == ("human_review",)  # parked at the interrupt, not past it


async def test_graph_resumes_to_end_on_approve(
    db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
):
    run = await _setup_run(
        db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
    )
    deps = _deps(db_session, git_service, deterministic_embedding_provider, vector_store)
    checkpointer = InMemorySaver()
    graph = build_planning_graph(deps, checkpointer)
    config = {"configurable": {"thread_id": str(run.id)}}

    await graph.ainvoke(_initial_state(run), config=config)
    await graph.ainvoke(Command(resume={"decision": "approve"}), config=config)

    state = await graph.aget_state(config)
    assert state.next == ()  # graph reached END
    assert state.values["approval_status"] == "approve"


async def test_citations_only_reference_retrieved_files(
    db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
):
    """Validates §16's citation-correctness rule holds even when the LLM
    (here, the template provider) tries to claim nothing — a real
    Ollama-backed run's citations are checked by the same `validate_plan`
    logic, exercised directly here without needing a live model."""
    run = await _setup_run(
        db_session, git_service, deterministic_embedding_provider, vector_store, sample_repo_path
    )
    deps = _deps(db_session, git_service, deterministic_embedding_provider, vector_store)
    checkpointer = InMemorySaver()
    graph = build_planning_graph(deps, checkpointer)
    config = {"configurable": {"thread_id": str(run.id)}}

    result = await graph.ainvoke(_initial_state(run), config=config)

    retrieved_paths = {c["file_path"] for c in result["retrieved_chunks"]}
    for citation in result["implementation_plan"]["citations"]:
        assert citation["file_path"] in retrieved_paths
    assert result["validation_errors"] == []
