import { apiFetch } from "@/shared/lib/api-client";

import type { ChatResponse, RepositoryStatusResponse, SearchResponse } from "./types";

export function registerRepository(url: string): Promise<RepositoryStatusResponse> {
  return apiFetch<RepositoryStatusResponse>("/repositories", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function triggerIndex(repositoryId: string): Promise<RepositoryStatusResponse> {
  return apiFetch<RepositoryStatusResponse>(`/repositories/${repositoryId}/index`, {
    method: "POST",
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

export function searchRepository(
  repositoryId: string,
  query: string,
  topK = 10,
): Promise<SearchResponse> {
  return apiFetch<SearchResponse>(`/repositories/${repositoryId}/search`, {
    method: "POST",
    body: JSON.stringify({ query, top_k: topK }),
  });
}

export function chatWithRepository(repositoryId: string, question: string): Promise<ChatResponse> {
  return apiFetch<ChatResponse>(`/repositories/${repositoryId}/chat`, {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

export { ACTIVE_STATUSES } from "./types";
export type {
  Citation,
  RepositoryEvent,
  RepositoryStatus,
  RepositoryStatusResponse,
  SearchResultItem,
} from "./types";
