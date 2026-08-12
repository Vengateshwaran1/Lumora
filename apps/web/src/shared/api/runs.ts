import { apiFetch } from "@/shared/lib/api-client";

import type { RunResponse, RunSummaryResponse } from "./types";

export function getRun(runId: string): Promise<RunResponse> {
  return apiFetch<RunResponse>(`/runs/${runId}`);
}

export function approveRun(runId: string, reason?: string): Promise<RunResponse> {
  return apiFetch<RunResponse>(`/runs/${runId}/approve`, {
    method: "POST",
    body: JSON.stringify(reason ? { reason } : {}),
  });
}

export function rejectRun(runId: string, reason?: string): Promise<RunResponse> {
  return apiFetch<RunResponse>(`/runs/${runId}/reject`, {
    method: "POST",
    body: JSON.stringify(reason ? { reason } : {}),
  });
}

export function regenerateRun(runId: string): Promise<RunSummaryResponse> {
  return apiFetch<RunSummaryResponse>(`/runs/${runId}/regenerate`, {
    method: "POST",
  });
}
