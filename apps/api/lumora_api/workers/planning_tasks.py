"""arq task: runs the Planning Agent's LangGraph graph up to (and pausing
at) the human-review interrupt. Registered as `RUN_ISSUE_PLAN` — see
`workers/task_names.py`/`workers/settings.py`.

An interrupt is the *expected* pause outcome, not a failure: LangGraph's
`interrupt()` doesn't raise, it pauses execution and returns normally with
the pending interrupt recorded in the checkpoint — `human_review`
(agents/planning/graph.py) already writes `Run.status = awaiting_approval`
to Postgres *before* calling `interrupt()`, specifically so a worker crash
in the window between "job dequeued" and "interrupt reached" still leaves
a recoverable, correctly-labeled run rather than one stuck at `running`
forever.
"""

import logging
import time
import uuid
from typing import Any

from lumora_api.agents.planning.graph import PlanningDeps, build_planning_graph
from lumora_api.core.container import (
    get_embedding_provider,
    get_git_service,
    get_planning_provider,
    get_reranker,
    get_vector_store,
)
from lumora_api.core.time import utcnow
from lumora_api.infrastructure.database import get_session_factory
from lumora_api.infrastructure.models import Run, RunStatus

logger = logging.getLogger(__name__)


async def run_issue_plan(ctx: dict[str, Any], run_id_str: str) -> dict[str, Any]:
    run_id = uuid.UUID(run_id_str)
    session_factory = get_session_factory()
    started = time.monotonic()

    async with session_factory() as session:
        run = await session.get(Run, run_id)
        if run is None:
            raise ValueError(f"Run {run_id} not found")
        run.status = RunStatus.RUNNING
        run.started_at = utcnow()
        await session.commit()

        deps = PlanningDeps(
            session=session,
            embedding_provider=get_embedding_provider(),
            vector_store=get_vector_store(),
            reranker=get_reranker(),
            planning_provider=get_planning_provider(),
            git_service=get_git_service(),
        )

        try:
            graph = build_planning_graph(deps, ctx["checkpointer"])
            initial_state = {
                "run_id": run_id_str,
                "repository_id": str(run.repository_id),
                "issue_id": str(run.issue_id),
            }
            await graph.ainvoke(
                initial_state, config={"configurable": {"thread_id": run_id_str}}
            )
        except Exception as exc:
            logger.exception("Planning run %s failed", run_id)
            await session.rollback()
            failed_run = await session.get(Run, run_id)
            if failed_run is not None:
                failed_run.status = RunStatus.FAILED
                failed_run.error_message = str(exc)
                failed_run.completed_at = utcnow()
                await session.commit()
            raise

    logger.info("Planning run %s reached human review in %.2fs", run_id, time.monotonic() - started)
    return {"run_id": run_id_str}
