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
