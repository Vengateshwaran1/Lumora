import { apiFetch } from "@/shared/lib/api-client";

import type { IssueResponse, RunSummaryResponse } from "./types";

export function listIssues(repositoryId: string): Promise<IssueResponse[]> {
  return apiFetch<IssueResponse[]>(`/repositories/${repositoryId}/issues`);
}

export function getIssue(repositoryId: string, issueId: string): Promise<IssueResponse> {
  return apiFetch<IssueResponse>(`/repositories/${repositoryId}/issues/${issueId}`);
}

/** Fire-and-forget background sync — 202, body `{status: "syncing"}`. No
 * polling endpoint for sync completion this milestone; callers invalidate
 * the issues list query after a short delay or on next visit. */
export function syncIssues(repositoryId: string): Promise<{ status: string }> {
  return apiFetch<{ status: string }>(`/repositories/${repositoryId}/issues/sync`, {
    method: "POST",
  });
}

export function generatePlan(
  repositoryId: string,
  issueId: string,
): Promise<RunSummaryResponse> {
  return apiFetch<RunSummaryResponse>(`/repositories/${repositoryId}/issues/${issueId}/plan`, {
    method: "POST",
  });
}
