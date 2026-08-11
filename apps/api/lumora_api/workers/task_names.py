"""arq job-function names shared between the enqueue side
(`infrastructure.jobs.arq_queue.ArqJobQueue`) and the worker side
(`workers.settings.WorkerSettings.functions`) — a single source so a typo
in one doesn't silently produce a job neither side recognizes.
"""

RUN_FULL_INDEX = "run_full_index"
RUN_INCREMENTAL_INDEX = "run_incremental_index"
