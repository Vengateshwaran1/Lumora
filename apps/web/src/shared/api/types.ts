/** Hand-written types mirroring `apps/api/lumora_api/api/v1/schemas.py` and
 * `infrastructure/models.py::RepositoryStatus`. No OpenAPI codegen yet
 * (ARCHITECTURE.md §10) — keep this file in sync by hand when the backend
 * schema changes. */

export type RepositoryStatus = "pending" | "queued" | "cloning" | "indexing" | "ready" | "failed";

/** Statuses where indexing is actively running. */
export const ACTIVE_STATUSES: readonly RepositoryStatus[] = ["queued", "cloning", "indexing"];

export interface RepositoryStatusResponse {
  id: string;
  url: string;
  name: string;
  full_name: string | null;
  status: RepositoryStatus;
  default_branch: string | null;
  last_indexed_commit: string | null;
  index_started_at: string | null;
  index_completed_at: string | null;
  indexed_file_count: number;
  indexed_chunk_count: number;
  error_message: string | null;
}

export interface SearchResultItem {
  chunk_id: string;
  file_path: string;
  language: string;
  symbol: string | null;
  kind: string;
  start_line: number;
  end_line: number;
  score: number;
  content: string;
}

export interface SearchResponse {
  results: SearchResultItem[];
}

export interface Citation {
  file_path: string;
  symbol: string | null;
  kind: string;
  start_line: number;
  end_line: number;
  score: number;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
}

/** Payloads published on the repository SSE channel
 * (`application/jobs/events.py`, `workers/tasks.py`,
 * `incremental_index_repository.py`). Fire-and-forget — a client connecting
 * after an event fires will not see it; polling `/index-status` remains the
 * source of truth. */
export type RepositoryEvent =
  | { event: "index.queued"; data: Record<string, never> }
  | { event: "index.started"; data: Record<string, never> }
  | {
      event: "index.files.discovered";
      data: { count: number; base_sha: string | null; after_sha: string | null };
    }
  | { event: "index.file.completed"; data: { path: string; status: string } }
  | {
      event: "index.completed";
      data: {
        duration_seconds: number;
        no_op: boolean;
        fell_back_to_full_index: boolean;
        files_discovered: number;
        files_added: number;
        files_modified: number;
        files_deleted: number;
        files_renamed: number;
        chunks_created: number;
        chunks_deleted: number;
        errors: number;
      };
    }
  | { event: "index.failed"; data: { error: string } };

/** GitHub issue synced for a repository (Planning Agent, M3). Mirrors
 * `apps/api/.../schemas.py::IssueResponse`. */
export interface IssueResponse {
  id: string;
  repository_id: string;
  number: number;
  title: string;
  body: string | null;
  author: string | null;
  labels: string[];
  state: string;
  html_url: string;
  github_created_at: string | null;
  github_updated_at: string | null;
  github_closed_at: string | null;
  synced_at: string;
}

export type RunStatus =
  | "queued"
  | "running"
  | "awaiting_approval"
  | "plan_approved"
  | "rejected"
  | "failed";

export type RunType = "planning";

/** Statuses where the run should keep being polled. */
export const ACTIVE_RUN_STATUSES: readonly RunStatus[] = ["queued", "running"];

/** A citation grounding one claim in the implementation plan to a specific
 * file range — distinct shape from the chat `Citation` above (no `symbol`/
 * `kind`/`score`, has `claim`), so it's named separately to avoid clashing. */
export interface PlanCitation {
  file_path: string;
  start_line: number;
  end_line: number;
  claim: string;
}

export interface ImplementationStep {
  step_number: number;
  description: string;
  affected_files: string[];
  affected_symbols: string[];
  reason: string;
  depends_on_steps: number[];
  verification_method: string;
}

export interface ImplementationPlan {
  summary: string;
  understanding: string;
  affected_files: string[];
  affected_components: string[];
  implementation_steps: ImplementationStep[];
  dependencies: string[];
  database_changes: string[];
  api_changes: string[];
  frontend_changes: string[];
  testing_strategy: string;
  security_considerations: string[];
  performance_considerations: string[];
  risks: string[];
  assumptions: string[];
  acceptance_criteria: string[];
  citations: PlanCitation[];
  confidence: number; // 0..1
}

export interface RunResponse {
  id: string;
  repository_id: string;
  issue_id: string | null;
  run_type: RunType;
  status: RunStatus;
  implementation_plan: ImplementationPlan | null;
  validation_errors: string[];
  metrics: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface RunSummaryResponse {
  run_id: string;
  status: RunStatus;
}

/** Payload published on the run SSE channel. Unlike `RepositoryEvent`, there
 * is no fully-enumerated union yet — in practice only `"run.queued"` fires
 * (published at enqueue time). Typed loosely on purpose; polling
 * `GET /runs/{id}` remains the source of truth (see `run-events.ts`). */
export interface RunEvent {
  event: string;
  data: Record<string, unknown>;
}
