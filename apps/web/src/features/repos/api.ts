import { apiFetch } from "@/shared/lib/api-client";

export type RepositoryStatus = "pending" | "queued" | "cloning" | "indexing" | "ready" | "failed";

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

export function registerRepository(url: string): Promise<RepositoryStatusResponse> {
  return apiFetch<RepositoryStatusResponse>("/repositories", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function getIndexStatus(repositoryId: string): Promise<RepositoryStatusResponse> {
  return apiFetch<RepositoryStatusResponse>(`/repositories/${repositoryId}/index-status`);
}

export function triggerReindex(repositoryId: string): Promise<RepositoryStatusResponse> {
  return apiFetch<RepositoryStatusResponse>(`/repositories/${repositoryId}/reindex`, {
    method: "POST",
  });
}

/** Statuses where indexing is actively running — the UI polls while any
 * tracked repo is in one of these, per milestone-2 spec §10 ("whether
 * indexing is running"). */
export const ACTIVE_STATUSES: readonly RepositoryStatus[] = ["queued", "cloning", "indexing"];
