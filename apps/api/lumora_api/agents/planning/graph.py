"""The Planning Agent's LangGraph graph (Milestone 3 §5):

START -> load_issue -> analyze_issue -> generate_search_queries ->
retrieve_context -> expand_code_graph -> retrieve_history -> build_context
-> generate_plan -> validate_plan -> human_review (interrupt) -> END

Nodes are closures over a `PlanningDeps` bundle rather than free functions
reading a global container — each run's worker task (or the API process,
for approve/reject) builds one `PlanningDeps` (one DB session, one set of
provider instances) and calls `build_planning_graph(deps, checkpointer)`,
matching how `workers/tasks.py`'s indexing jobs build their own
dependencies without going through FastAPI's `Depends`.

Read-only, by construction: every node only calls `search_repository`,
`expand_dependencies`, `Issue`/`IndexedFile` reads, and
`GitService.search_commit_log` (all read paths) — nothing here can write
to GitHub, write source files, or touch git in a mutating way. See
docs/architecture/adr for the read-only-this-milestone rationale.
"""

import uuid
from dataclasses import dataclass
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.agents.planning.schemas import ImplementationPlan, IssueAnalysis, SearchQueries
from lumora_api.agents.planning.state import PlannerState
from lumora_api.application.graph.build_symbol_graph import build_symbol_graph
from lumora_api.application.graph.expand_dependencies import expand_dependencies
from lumora_api.application.search.search_repository import search_repository
from lumora_api.domain.retrieval import RetrievedChunk
from lumora_api.infrastructure.embeddings.base import EmbeddingProvider
from lumora_api.infrastructure.llm.planning import PlanningProvider
from lumora_api.infrastructure.models import IndexedFile, Issue, Repository, Run, RunStatus
from lumora_api.infrastructure.retrieval.reranker.base import Reranker
from lumora_api.infrastructure.vcs.git_service import GitService
from lumora_api.infrastructure.vector_store.qdrant_store import QdrantVectorStore

_MAX_RETRIEVED_CHUNKS = 15
_MAX_HISTORICAL_ISSUES = 5
_MAX_HISTORICAL_COMMITS = 8
_MAX_PLAN_REGENERATION_ATTEMPTS = 1


@dataclass
class PlanningDeps:
    session: AsyncSession
    embedding_provider: EmbeddingProvider
    vector_store: QdrantVectorStore
    reranker: Reranker
    planning_provider: PlanningProvider
    git_service: GitService


def build_planning_graph(
    deps: PlanningDeps, checkpointer: Any
) -> CompiledStateGraph[Any, Any, Any]:
    graph = StateGraph(PlannerState)

    graph.add_node("load_issue", _load_issue(deps))
    graph.add_node("analyze_issue", _analyze_issue(deps))
    graph.add_node("generate_search_queries", _generate_search_queries(deps))
    graph.add_node("retrieve_context", _retrieve_context(deps))
    graph.add_node("expand_code_graph", _expand_code_graph(deps))
    graph.add_node("retrieve_history", _retrieve_history(deps))
    graph.add_node("build_context", _build_context(deps))
    graph.add_node("generate_plan", _generate_plan(deps))
    graph.add_node("validate_plan", _validate_plan(deps))
    graph.add_node("human_review", _human_review(deps))

    graph.add_edge(START, "load_issue")
    graph.add_edge("load_issue", "analyze_issue")
    graph.add_edge("analyze_issue", "generate_search_queries")
    graph.add_edge("generate_search_queries", "retrieve_context")
    graph.add_edge("retrieve_context", "expand_code_graph")
    graph.add_edge("expand_code_graph", "retrieve_history")
    graph.add_edge("retrieve_history", "build_context")
    graph.add_edge("build_context", "generate_plan")
    graph.add_edge("generate_plan", "validate_plan")
    graph.add_edge("validate_plan", "human_review")
    graph.add_edge("human_review", END)

    return graph.compile(checkpointer=checkpointer)


def _incr_llm_calls(state: PlannerState) -> dict[str, Any]:
    metrics = dict(state.get("metrics", {}))
    metrics["llm_calls"] = metrics.get("llm_calls", 0) + 1
    return metrics


# --- load_issue -------------------------------------------------------


def _load_issue(deps: PlanningDeps) -> Any:
    async def node(state: PlannerState) -> dict[str, Any]:
        issue = await deps.session.get(Issue, uuid.UUID(state["issue_id"]))
        if issue is None:
            raise ValueError(f"Issue {state['issue_id']} not found")
        return {
            "issue_title": issue.title,
            "issue_body": issue.body or "",
            "issue_metadata": {
                "number": issue.number,
                "author": issue.author,
                "labels": issue.labels,
                "state": issue.state,
                "html_url": issue.html_url,
            },
            "metrics": {"llm_calls": 0},
        }

    return node


# --- analyze_issue ------------------------------------------------------


def _analyze_issue(deps: PlanningDeps) -> Any:
    async def node(state: PlannerState) -> dict[str, Any]:
        prompt = (
            "Analyze this GitHub issue for a software repository. Extract the problem, "
            "desired behavior, requirements, constraints, acceptance criteria, ambiguities, "
            "and which parts of the system are likely affected. Do not propose code changes yet "
            "— understand the issue first.\n\n"
            f"Title: {state['issue_title']}\n\nBody:\n{state['issue_body']}"
        )
        analysis = await deps.planning_provider.generate_structured(
            prompt=prompt, schema=IssueAnalysis
        )
        return {
            "issue_analysis": analysis.model_dump(),
            "metrics": _incr_llm_calls(state),
        }

    return node


# --- generate_search_queries --------------------------------------------


def _generate_search_queries(deps: PlanningDeps) -> Any:
    async def node(state: PlannerState) -> dict[str, Any]:
        analysis = state.get("issue_analysis", {})
        affected_guess = ", ".join(analysis.get("potentially_affected_components", []))
        prompt = (
            "Generate focused repository search queries to find the code relevant to this "
            "issue — not the whole issue text verbatim, but targeted terms (e.g. "
            "'authentication middleware', 'user model', 'login endpoint'). 2-6 queries.\n\n"
            f"Issue: {state['issue_title']}\n"
            f"Problem: {analysis.get('problem', '')}\n"
            f"Affected components (guess): {affected_guess}"
        )
        result = await deps.planning_provider.generate_structured(
            prompt=prompt, schema=SearchQueries
        )
        return {
            "search_queries": result.queries,
            "metrics": _incr_llm_calls(state),
        }

    return node


# --- retrieve_context -----------------------------------------------------


def _retrieve_context(deps: PlanningDeps) -> Any:
    async def node(state: PlannerState) -> dict[str, Any]:
        repository_id = uuid.UUID(state["repository_id"])
        by_id: dict[str, RetrievedChunk] = {}
        for query in state.get("search_queries", []):
            chunks = await search_repository(
                repository_id=repository_id,
                query=query,
                top_k=8,
                session=deps.session,
                embedding_provider=deps.embedding_provider,
                vector_store=deps.vector_store,
                reranker=deps.reranker,
            )
            for chunk in chunks:
                existing = by_id.get(chunk.chunk_id)
                if existing is None or chunk.score > existing.score:
                    by_id[chunk.chunk_id] = chunk

        ranked = sorted(by_id.values(), key=lambda c: c.score, reverse=True)
        top = ranked[:_MAX_RETRIEVED_CHUNKS]
        return {
            "retrieved_chunks": [_chunk_to_dict(c) for c in top],
            "related_files": sorted({c.file_path for c in top}),
            "metrics": {**state.get("metrics", {}), "retrieval_count": len(top)},
        }

    return node


def _chunk_to_dict(chunk: RetrievedChunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "file_path": chunk.file_path,
        "language": chunk.language,
        "symbol": chunk.symbol,
        "kind": chunk.kind,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "content": chunk.content,
        "score": chunk.score,
    }


# --- expand_code_graph ---------------------------------------------------


def _expand_code_graph(deps: PlanningDeps) -> Any:
    async def node(state: PlannerState) -> dict[str, Any]:
        repository_id = uuid.UUID(state["repository_id"])
        repository = await deps.session.get(Repository, repository_id)
        if repository is not None and repository.symbol_graph_built_at is None:
            await build_symbol_graph(repository_id=repository_id, session=deps.session)

        chunk_ids = [c["chunk_id"] for c in state.get("retrieved_chunks", [])]
        neighbors = await expand_dependencies(
            repository_id=repository_id, chunk_ids=chunk_ids, session=deps.session
        )
        return {"related_symbols": [_chunk_to_dict(c) for c in neighbors]}

    return node


# --- retrieve_history ------------------------------------------------------


def _retrieve_history(deps: PlanningDeps) -> Any:
    async def node(state: PlannerState) -> dict[str, Any]:
        repository_id = uuid.UUID(state["repository_id"])
        queries = state.get("search_queries", []) or [state["issue_title"]]
        current_issue_id = uuid.UUID(state["issue_id"])

        historical_issues = await _search_related_issues(
            deps.session, repository_id, current_issue_id, queries
        )
        historical_commits = await _search_commit_log(deps, repository_id, queries)

        return {
            "historical_issues": historical_issues,
            "historical_commits": historical_commits,
        }

    return node


async def _search_related_issues(
    session: AsyncSession,
    repository_id: uuid.UUID,
    current_issue_id: uuid.UUID,
    queries: list[str],
) -> list[dict[str, Any]]:
    seen: dict[int, dict[str, Any]] = {}
    for query in queries[:5]:
        term = query.strip()
        if len(term) < 3:
            continue
        result = await session.execute(
            select(Issue)
            .where(
                Issue.repository_id == repository_id,
                Issue.id != current_issue_id,
                (Issue.title.ilike(f"%{term}%")) | (Issue.body.ilike(f"%{term}%")),
            )
            .limit(_MAX_HISTORICAL_ISSUES)
        )
        for issue in result.scalars():
            seen[issue.number] = {
                "number": issue.number,
                "title": issue.title,
                "html_url": issue.html_url,
            }
        if len(seen) >= _MAX_HISTORICAL_ISSUES:
            break
    return list(seen.values())[:_MAX_HISTORICAL_ISSUES]


async def _search_commit_log(
    deps: PlanningDeps, repository_id: uuid.UUID, queries: list[str]
) -> list[dict[str, Any]]:
    if not deps.git_service.has_clone(repository_id):
        return []
    local_path = deps.git_service.repo_path(repository_id)

    seen: dict[str, dict[str, Any]] = {}
    for query in queries[:5]:
        term = query.strip()
        if len(term) < 3:
            continue
        for sha, subject in deps.git_service.search_commit_log(local_path, term, max_results=3):
            seen[sha] = {"sha": sha, "subject": subject}
        if len(seen) >= _MAX_HISTORICAL_COMMITS:
            break
    return list(seen.values())[:_MAX_HISTORICAL_COMMITS]


# --- build_context -----------------------------------------------------


def _build_context(deps: PlanningDeps) -> Any:
    async def node(state: PlannerState) -> dict[str, Any]:
        context = render_context(state)
        metrics = dict(state.get("metrics", {}))
        metrics["context_chars"] = len(context)
        metrics["approx_tokens"] = len(context) // 4
        return {"metrics": metrics}

    return node


def render_context(state: PlannerState) -> str:
    analysis = state.get("issue_analysis", {})
    parts = [
        f"# Issue: {state['issue_title']}",
        state.get("issue_body", ""),
        "",
        "## Analysis",
        f"Problem: {analysis.get('problem', '')}",
        f"Desired behavior: {analysis.get('desired_behavior', '')}",
        f"Requirements: {'; '.join(analysis.get('functional_requirements', []))}",
        "",
        "## Retrieved repository context",
    ]
    for chunk in state.get("retrieved_chunks", []):
        label = chunk.get("symbol") or chunk.get("kind")
        parts.append(
            f"[{chunk['file_path']}:{chunk['start_line']}-{chunk['end_line']}] {label}\n"
            f"{chunk['content']}\n"
        )

    related_symbols = state.get("related_symbols", [])
    if related_symbols:
        parts.append("## Related symbols (heuristic reference graph — not resolved calls)")
        for chunk in related_symbols:
            label = chunk.get("symbol") or chunk.get("kind")
            span = f"{chunk['file_path']}:{chunk['start_line']}-{chunk['end_line']}"
            parts.append(f"[{span}] {label}")

    historical_issues = state.get("historical_issues", [])
    if historical_issues:
        parts.append("## Related past issues")
        for issue in historical_issues:
            parts.append(f"#{issue['number']} {issue['title']} ({issue['html_url']})")

    historical_commits = state.get("historical_commits", [])
    if historical_commits:
        parts.append("## Related commit history")
        for commit in historical_commits:
            parts.append(f"{commit['sha']} {commit['subject']}")

    return "\n".join(parts)


# --- generate_plan -----------------------------------------------------


def _generate_plan(deps: PlanningDeps) -> Any:
    async def node(state: PlannerState) -> dict[str, Any]:
        context = render_context(state)
        prompt = (
            "Using ONLY the repository context below, produce a structured implementation "
            "plan for this issue. Every citation must reference a file:line range that "
            "actually appears in the 'Retrieved repository context' section. Do not invent "
            "file names or line numbers. If something is uncertain, say so in "
            "'assumptions' rather than stating it as fact.\n\n" + context
        )
        plan = await deps.planning_provider.generate_structured(
            prompt=prompt, schema=ImplementationPlan
        )
        return {
            "implementation_plan": plan.model_dump(),
            "risks": plan.risks,
            "assumptions": plan.assumptions,
            "confidence": plan.confidence,
            "metrics": _incr_llm_calls(state),
        }

    return node


# --- validate_plan -----------------------------------------------------


def _validate_plan(deps: PlanningDeps) -> Any:
    async def node(state: PlannerState) -> dict[str, Any]:
        errors = await _validate(deps.session, uuid.UUID(state["repository_id"]), state)

        if errors and state.get("metrics", {}).get("regeneration_attempts", 0) < (
            _MAX_PLAN_REGENERATION_ATTEMPTS
        ):
            context = render_context(state)
            prompt = (
                "Your previous implementation plan had validation errors:\n"
                + "\n".join(f"- {e}" for e in errors)
                + "\n\nFix these — every citation and affected_files entry must correspond to "
                "the repository context below, and implementation_steps.depends_on_steps must "
                "only reference earlier step numbers. Regenerate the full plan.\n\n" + context
            )
            plan = await deps.planning_provider.generate_structured(
                prompt=prompt, schema=ImplementationPlan
            )
            metrics = _incr_llm_calls(state)
            metrics["regeneration_attempts"] = metrics.get("regeneration_attempts", 0) + 1
            new_state: PlannerState = {**state, "implementation_plan": plan.model_dump()}
            errors = await _validate(deps.session, uuid.UUID(state["repository_id"]), new_state)
            return {
                "implementation_plan": plan.model_dump(),
                "risks": plan.risks,
                "assumptions": plan.assumptions,
                "confidence": plan.confidence if not errors else min(plan.confidence, 0.4),
                "validation_errors": errors,
                "metrics": metrics,
            }

        confidence = state.get("confidence", 0.5)
        return {
            "validation_errors": errors,
            "confidence": confidence if not errors else min(confidence, 0.4),
        }

    return node


async def _validate(
    session: AsyncSession, repository_id: uuid.UUID, state: PlannerState
) -> list[str]:
    plan = state.get("implementation_plan")
    if not plan:
        return ["No implementation plan was generated."]

    errors: list[str] = []

    retrieved_paths = {c["file_path"] for c in state.get("retrieved_chunks", [])}
    related_paths = retrieved_paths | {c["file_path"] for c in state.get("related_symbols", [])}

    for citation in plan.get("citations", []):
        path = citation.get("file_path")
        if path not in related_paths:
            errors.append(f"Citation references {path!r}, which was never retrieved.")

    affected_files = plan.get("affected_files", [])
    if affected_files:
        result = await session.execute(
            select(IndexedFile.path).where(
                IndexedFile.repository_id == repository_id, IndexedFile.path.in_(affected_files)
            )
        )
        existing_paths = set(result.scalars().all())
        for path in affected_files:
            if path not in existing_paths:
                errors.append(f"affected_files references {path!r}, not found in the repo.")

    step_numbers = {step["step_number"] for step in plan.get("implementation_steps", [])}
    for step in plan.get("implementation_steps", []):
        for dep in step.get("depends_on_steps", []):
            if dep not in step_numbers or dep >= step["step_number"]:
                errors.append(
                    f"Step {step['step_number']} depends_on_steps references invalid step {dep}."
                )

    return errors


# --- human_review (interrupt) -----------------------------------------------


def _human_review(deps: PlanningDeps) -> Any:
    async def node(state: PlannerState) -> dict[str, Any]:
        run = await deps.session.get(Run, uuid.UUID(state["run_id"]))
        if run is not None:
            run.status = RunStatus.AWAITING_APPROVAL
            run.implementation_plan = state.get("implementation_plan")
            run.validation_errors = state.get("validation_errors", [])
            run.metrics = state.get("metrics", {})
            await deps.session.commit()

        decision = interrupt(
            {
                "message": "Plan awaiting human approval.",
                "plan": state.get("implementation_plan"),
            }
        )
        return {"approval_status": decision.get("decision", "pending")}

    return node
