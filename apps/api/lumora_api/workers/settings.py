"""arq worker entry point: `arq lumora_api.workers.settings.WorkerSettings`
(see `infra/docker/api.Dockerfile` / `docker-compose.yml`'s `worker`
service).
"""

from typing import Any

from arq.connections import RedisSettings

from lumora_api.core.config import get_settings
from lumora_api.core.container import build_checkpointer
from lumora_api.core.logging import configure_logging
from lumora_api.workers.planning_tasks import run_issue_plan
from lumora_api.workers.tasks import run_full_index, run_incremental_index


async def _on_startup(ctx: dict[str, Any]) -> None:
    configure_logging(get_settings())
    ctx["checkpointer_pool"], ctx["checkpointer"] = await build_checkpointer()


async def _on_shutdown(ctx: dict[str, Any]) -> None:
    await ctx["checkpointer_pool"].close()


class WorkerSettings:
    functions = [run_full_index, run_incremental_index, run_issue_plan]
    on_startup = _on_startup
    on_shutdown = _on_shutdown

    _settings = get_settings()
    redis_settings = RedisSettings(
        host=_settings.redis_host, port=_settings.redis_port, database=_settings.redis_db
    )
    # A repo-level advisory lock (incremental_index_repository) already
    # serializes concurrent jobs for the same repository; this just caps
    # how many *different* repos' jobs run at once on one worker process.
    max_jobs = 4
