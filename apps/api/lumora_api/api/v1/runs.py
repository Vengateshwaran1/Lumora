"""Agent run endpoints (Milestone 3 §17/§20) — reading run status/streaming
progress, and the human-approval actions that resume the Planning Agent's
LangGraph interrupt. `runs` (Postgres) is the source of truth the frontend
reads; the LangGraph checkpointer is internal execution state, touched
only by the resume endpoints below and the worker task.
"""

import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langgraph.types import Command

from lumora_api.agents.planning.graph import PlanningDeps, build_planning_graph
from lumora_api.api.v1.schemas import RunDecisionRequest, RunResponse, RunSummaryResponse
from lumora_api.core.container import (
    ArqRedisDep,
    CheckpointerDep,
    DbSessionDep,
    EmbeddingProviderDep,
    JobQueueDep,
    PlanningProviderDep,
    RerankerDep,
    VectorStoreDep,
    get_git_service,
)
from lumora_api.core.time import utcnow
from lumora_api.infrastructure.models import Run, RunStatus, RunType
from lumora_api.infrastructure.runs.run_events import run_channel_name

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: uuid.UUID, session: DbSessionDep) -> Run:
    return await _require_run(session, run_id)


@router.get("/{run_id}/stream")
async def stream_run(
    run_id: uuid.UUID, session: DbSessionDep, redis: ArqRedisDep
) -> StreamingResponse:
    """SSE progress stream — same fire-and-forget shape as
    `repositories.py`'s `_event_stream`, keyed on the run channel instead
    of the repository channel (Milestone 3 §20 reuses this infrastructure
    rather than building a second one)."""
    await _require_run(session, run_id)
    return StreamingResponse(_event_stream(redis, run_id), media_type="text/event-stream")


async def _event_stream(redis: ArqRedisDep, run_id: uuid.UUID) -> AsyncIterator[str]:
    pubsub = redis.pubsub()
    channel = run_channel_name(run_id)
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            data = message["data"]
            text = data.decode("utf-8") if isinstance(data, bytes) else str(data)
            yield f"data: {text}\n\n"
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()  # type: ignore[no-untyped-call]


@router.post("/{run_id}/approve", response_model=RunResponse)
async def approve_run(
    run_id: uuid.UUID,
    body: RunDecisionRequest,
    session: DbSessionDep,
    checkpointer: CheckpointerDep,
    embedding_provider: EmbeddingProviderDep,
    vector_store: VectorStoreDep,
    reranker: RerankerDep,
    planning_provider: PlanningProviderDep,
) -> Run:
    del body  # reason is stored nowhere yet — accepted for forward-compat with the UI's reject flow
    return await _resume(
        run_id=run_id,
        decision="approve",
        resulting_status=RunStatus.PLAN_APPROVED,
        session=session,
        checkpointer=checkpointer,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        reranker=reranker,
        planning_provider=planning_provider,
    )


@router.post("/{run_id}/reject", response_model=RunResponse)
async def reject_run(
    run_id: uuid.UUID,
    body: RunDecisionRequest,
    session: DbSessionDep,
    checkpointer: CheckpointerDep,
    embedding_provider: EmbeddingProviderDep,
    vector_store: VectorStoreDep,
    reranker: RerankerDep,
    planning_provider: PlanningProviderDep,
) -> Run:
    del body
    return await _resume(
        run_id=run_id,
        decision="reject",
        resulting_status=RunStatus.REJECTED,
        session=session,
        checkpointer=checkpointer,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        reranker=reranker,
        planning_provider=planning_provider,
    )


@router.post("/{run_id}/regenerate", response_model=RunSummaryResponse, status_code=202)
async def regenerate_run(
    run_id: uuid.UUID, session: DbSessionDep, job_queue: JobQueueDep
) -> dict[str, object]:
    """Does not rewind the existing LangGraph thread — interrupt/resume
    isn't built for replaying a prior step. Creates a fresh `Run` for the
    same issue and enqueues a new planning job; the original run is left
    untouched (still inspectable in its `awaiting_approval` state)."""
    original = await _require_run(session, run_id)

    new_run = Run(
        repository_id=original.repository_id,
        issue_id=original.issue_id,
        run_type=RunType.PLANNING,
        status=RunStatus.QUEUED,
    )
    session.add(new_run)
    await session.flush()
    new_run.langgraph_thread_id = str(new_run.id)
    await session.commit()

    await job_queue.enqueue_issue_plan(run_id=new_run.id)
    return {"run_id": new_run.id, "status": new_run.status}


async def _resume(
    *,
    run_id: uuid.UUID,
    decision: str,
    resulting_status: RunStatus,
    session: DbSessionDep,
    checkpointer: CheckpointerDep,
    embedding_provider: EmbeddingProviderDep,
    vector_store: VectorStoreDep,
    reranker: RerankerDep,
    planning_provider: PlanningProviderDep,
) -> Run:
    run = await _require_run(session, run_id)
    if run.status != RunStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=409, detail=f"Run {run_id} is not awaiting approval (status={run.status})"
        )

    deps = PlanningDeps(
        session=session,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        reranker=reranker,
        planning_provider=planning_provider,
        git_service=get_git_service(),
    )
    graph = build_planning_graph(deps, checkpointer)
    config = {"configurable": {"thread_id": str(run_id)}}
    resume: Command[Any] = Command(resume={"decision": decision})
    await graph.ainvoke(resume, config=config)  # type: ignore[call-overload]

    run.status = resulting_status
    run.completed_at = utcnow()
    await session.commit()
    await session.refresh(run)
    return run


async def _require_run(session: DbSessionDep, run_id: uuid.UUID) -> Run:
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
