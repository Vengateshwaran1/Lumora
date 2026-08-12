# Milestone 3 — Issue Understanding + Planning Agent

## Context

Builds the vertical slice from [ARCHITECTURE.md §14](ARCHITECTURE.md#14-development-roadmap)'s
M3: the first real AI agent — issue → structured implementation plan,
grounded in the Milestone 1 RAG pipeline and a new Postgres symbol graph,
gated behind human approval. Follows the same format as
[milestone-1-rag-pipeline.md](milestone-1-rag-pipeline.md) /
[milestone-2-incremental-indexing.md](milestone-2-incremental-indexing.md).

```
GitHub Issue → Sync → Load Issue → Analyze Issue → Generate Search Queries
  → Retrieve Repository Context (hybrid search) → Expand Code Graph
  → Retrieve Historical Context → Build Context → Generate Implementation Plan
  → Validate Plan → Human Review (interrupt) → END
  → Approve → plan_approved | Reject → rejected | Regenerate → new run
```

**Strictly read-only.** The Planning Agent has no shell execution, no file
write, no GitHub write API access, no commit/branch/PR creation — see the
[ADR](adr/0001-planning-agent-read-only.md) for why, and for the two
scope deviations from the milestone brief below.

---

## Deviations from the milestone brief, and why

**§10 "existing PostgreSQL symbol graph" — didn't exist, built a minimal
heuristic version.** M1/M2 explicitly deferred `symbols`/`symbol_edges`
(`infrastructure/models.py`'s docstring, and milestone-2's own "Deviations"
section). A real AST-resolved call graph (per-language parsing, cross-file
symbol resolution) is a multi-week feature on its own. Instead:
`SymbolEdge` rows keyed directly on `chunks.id` (no separate `symbols`
table — `Chunk` already carries `symbol`/`kind`/`file_path`/lines),
populated by `application/graph/build_symbol_graph.py` via regex
name-reference matching (a chunk's content mentioning another chunk's
symbol name becomes a `references` edge) and import-line-to-file-stem
matching (`imports` edges). This is explicitly a **heuristic reference
graph, not a call graph** — never described as one in code, prompts, or
UI. See the ADR for the full reasoning.

**§2/§9 "existing GitHub App integration" — no functional connect flow
existed.** `installation_id` was defined on `Repository` but never
populated; there was no App-install UI or OAuth callback. Building a real
GitHub App install flow needs a public callback URL not available in this
project's local-dev setup. Used instead: a single `GITHUB_TOKEN` (PAT)
setting, applied at the one place clone/fetch URLs are resolved
(`infrastructure/github/clone_auth.py::resolve_clone_url`) and at issue-sync
time (`infrastructure/github/issues_client.py`). Priority order:
`installation_id` (App token, if ever configured) → `GITHUB_TOKEN` (PAT) →
plain URL (public repos). The existing `GitHubAppAuth`/
`authenticated_clone_url` code from Milestone 2 is unchanged, just finally
wired up as the first-priority path.

**Route prefix stays `/repositories`, not `/repos`.** Issues and the plan
trigger live under `/api/v1/repositories/{id}/issues/...`, matching M1/M2's
established prefix rather than introducing a parallel one for one resource
— same reasoning M2's own doc gives for `/index-status`/`/reindex`.

**No `GET /runs` list endpoint.** Only `GET /runs/{id}` exists — a run is
always reached via the issue that triggered it (`POST .../issues/{id}/plan`
returns the `run_id`). A cross-repository run history list is deferred;
nothing in the milestone brief's verification gate needs it.

**No PR/commit-message embedding index for historical context.** §11 asks
for "relevant historical information... previous issues, previous PRs,
commit messages." PRs aren't synced in this milestone (no PR model exists
yet — that's M5). Historical context is: other `Issue` rows matched by
keyword overlap against the generated search queries (SQL `ILIKE`, no new
embedding index — small scale, and adding a second retrieval system for
this was explicitly out of scope per §9), plus `git log --grep` over the
already-cloned repository (`GitService.search_commit_log`, read-only, no
GitHub API call). This is a real gap, not silently padded — the frontend
and the doc here both say so rather than implying PR history was searched.

**LangGraph checkpointer setup runs at process startup, not via Alembic.**
`AsyncPostgresSaver.setup()` creates LangGraph's own checkpoint tables —
called once in both `main.py`'s lifespan and `workers/settings.py`'s
`on_startup`. ARCHITECTURE.md §12 says migrations never run on app
startup; this is a deliberate, documented exception because it's
LangGraph-owned infrastructure with no Alembic-style deploy step of its
own, and `.setup()` is idempotent (safe on every process start, including
concurrent API+worker startup).

---

## Planner state

`agents/planning/state.py::PlannerState` — a `TypedDict`, not an untyped
dict, used as the LangGraph `StateGraph`'s schema:

```
run_id, repository_id, issue_id
issue_title, issue_body, issue_metadata, issue_analysis
search_queries
retrieved_chunks, related_symbols, related_files
historical_issues, historical_commits
implementation_plan, risks, assumptions, confidence, validation_errors
approval_status
metrics
```

Chunk-shaped fields are plain `dict[str, Any]` (a `RetrievedChunkDict`
TypedDict), not `RetrievedChunk` dataclass instances — keeps the Postgres
checkpointer's JSON serialization free of custom-type concerns. Node
functions (`agents/planning/graph.py`) convert to/from `RetrievedChunk` at
the boundary with `application/search/search_repository.py`.

## LangGraph graph

`agents/planning/graph.py::build_planning_graph(deps, checkpointer)` —
nodes are closures over a `PlanningDeps` bundle (one DB session, one set of
provider instances) built once per run, not free functions reaching into a
global container — matches how `workers/tasks.py`'s indexing jobs build
their own dependencies outside FastAPI's `Depends`.

`load_issue → analyze_issue → generate_search_queries → retrieve_context →
expand_code_graph → retrieve_history → build_context → generate_plan →
validate_plan → human_review (interrupt) → END`

- **3 LLM calls** per run in the common case: `analyze_issue` (→
  `IssueAnalysis`), `generate_search_queries` (→ `SearchQueries`),
  `generate_plan` (→ `ImplementationPlan`). `validate_plan` may trigger one
  additional regeneration call if citations/affected-files/step-ordering
  fail validation (capped at 1 retry — see `_MAX_PLAN_REGENERATION_ATTEMPTS`).
- **`retrieve_context`** calls the *existing* M1
  `search_repository` once per generated query — no second retrieval
  system — dedups by `chunk_id`, keeps the top 15 by score.
- **`expand_code_graph`** calls `application/graph/expand_dependencies.py`
  over the retrieved chunk ids; lazily calls `build_symbol_graph` first if
  the repository's `symbol_graph_built_at` is unset (so a repo indexed
  before this migration doesn't need a full reindex to get a plan).
- **`build_context`** assembles one prompt string (issue + analysis +
  retrieved chunks + graph neighbors + history), tracked in `metrics` as
  `context_chars`/`approx_tokens` (`len(text) // 4` — no tokenizer
  dependency exists yet, so this is an approximation, not exact usage).
- **`human_review`** writes `Run.status = awaiting_approval` to Postgres
  **before** calling `interrupt()` — not only after the worker task catches
  the pause. This closes a crash-recovery gap: unlike indexing, there's no
  `/index-status`-style recompute for a run, so a worker dying in the
  window between "job dequeued" and "interrupt reached" must not leave the
  run stuck at `running` forever.

## Structured output + retry

`infrastructure/llm/planning.py::PlanningProvider` — one method,
`generate_structured(prompt, schema) -> T`, parallel to M1's `ChatProvider`
but returning a validated Pydantic model instead of prose.

- **`OllamaPlanningProvider`**: Ollama `/api/generate` with
  `format=<schema.model_json_schema()>` (Qwen's structured-output mode).
  Retries up to 3 times, feeding the validation error back into the prompt
  on `json.JSONDecodeError`/`pydantic.ValidationError`; raises
  `PlanGenerationError` after exhausting retries — never returns a
  malformed/partial instance.
- **`TemplatePlanningProvider`**: the offline default (`PLANNING_PROVIDER=
  template`, matching `EMBEDDING_PROVIDER=deterministic`/`CHAT_PROVIDER=
  extractive`'s "works with zero setup" convention). Each schema that needs
  an offline fallback implements `offline_default(prompt) -> Self`
  (`agents/planning/schemas.py`) — called via duck typing, so the provider
  itself has no business-schema knowledge. Offline defaults are
  deliberately conservative: empty `affected_files`/`citations`, low
  `confidence` — an offline default that claimed things about the
  repository it never looked at would itself be a hallucination.

## Plan validation (§16)

`agents/planning/graph.py::_validate` — pure function, no LLM:

- every `citations[].file_path` must be in the retrieved/graph-expanded
  chunk set
- every `affected_files` entry must exist in `IndexedFile` for the repo
- every `implementation_steps[].depends_on_steps` entry must reference an
  earlier step number

On failure: one regeneration attempt with the errors fed back into the
prompt; if still failing, the plan is kept with `validation_errors`
populated and `confidence` capped at 0.4 — never silently dropped or
fabricated around.

## Human approval

`api/v1/runs.py` — `runs` (Postgres) is the source of truth the frontend
polls, same role `Repository.status`/`/index-status` play for indexing;
the LangGraph checkpointer is internal execution state, touched only by
the worker task and the approve/reject endpoints.

- `POST /runs/{id}/approve` / `/reject`: resolves the compiled graph with
  the request-scoped `CheckpointerDep`, resumes via
  `graph.ainvoke(Command(resume={"decision": ...}), config=...)`. Since the
  only work after the interrupt is reaching `END`, this runs synchronously
  in the request (no queue) — then the endpoint reads back the final graph
  state and writes `Run.status` (`plan_approved`/`rejected`) itself.
  **Approving does not start coding** — that's M4; approval only changes
  the run's status.
- `POST /runs/{id}/regenerate`: does not rewind the existing LangGraph
  thread (interrupt/resume isn't built for replaying a prior step).
  Creates a new `Run` row for the same issue and enqueues a fresh
  `run_issue_plan` job; the original run is left untouched.

## Progress streaming

Reuses the M2 SSE infrastructure exactly — `infrastructure/runs/
run_events.py::RedisRunEventPublisher`/`run_channel_name` mirror
`infrastructure/jobs/redis_events.py`, just keyed on `run_id` instead of
`repository_id`. `GET /runs/{id}/stream` is fire-and-forget decoration,
same caveat as the repository event stream: a client connecting after an
event fired sees nothing before it. `GET /runs/{id}` polling is the
durable source of truth the frontend reconciles from.

## Cost/context metrics (§22)

`Run.metrics` (JSONB): `llm_calls`, `retrieval_count`, `context_chars`,
`approx_tokens`, `regeneration_attempts`. No token-exact accounting (no
tokenizer dependency yet) — approximated from character count, documented
as such rather than presented as precise.

## Evaluation (§25)

`tests/eval/planning_eval.py` — a small fixture repository with a
hand-written set of issues (feature/bugfix/refactor), each with expected
affected files/components. Not a CI gate (LLM-quality regression testing
against a moving local model isn't a green/red CI signal) — run manually
to sanity-check citation correctness, affected-file accuracy, and
hallucination rate before enabling `PLANNING_PROVIDER=ollama` for real use.
