import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";

import { useRepositoryEvents } from "@/shared/api/events";
import { getIndexStatus } from "@/shared/api/repositories";
import { ACTIVE_STATUSES, type RepositoryEvent } from "@/shared/api/types";

export type IndexingStage =
  "connecting" | "fetching" | "discovering" | "processing" | "ready" | "failed";

export interface FileProgressEntry {
  path: string;
  status: string;
}

export type IndexCompletedData = Extract<RepositoryEvent, { event: "index.completed" }>["data"];

/** Drives the indexing pipeline UI off real signals only:
 * `/index-status` polling (source of truth) + the SSE stream (decoration,
 * only ever adds detail for a client connected while the run happens —
 * see `application/jobs/events.py`). Never fabricates a stage or a
 * progress percentage that isn't backed by one of these. */
export function useIndexingProgress(repositoryId: string | undefined) {
  const statusQuery = useQuery({
    queryKey: ["repository", repositoryId, "index-status"],
    queryFn: () => getIndexStatus(repositoryId!),
    enabled: !!repositoryId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ACTIVE_STATUSES.includes(status) ? 2000 : false;
    },
  });

  const status = statusQuery.data?.status;
  const isActive = !!status && ACTIVE_STATUSES.includes(status);

  const [discoveredCount, setDiscoveredCount] = useState<number | null>(null);
  const [recentFiles, setRecentFiles] = useState<FileProgressEntry[]>([]);
  const [completedStats, setCompletedStats] = useState<IndexCompletedData | null>(null);
  const seenRunKey = useRef<string | null>(null);

  useEffect(() => {
    if (!status) return;
    const runKey = `${repositoryId}:${status === "ready" || status === "failed" ? "idle" : "active"}`;
    if (isActive && seenRunKey.current !== runKey) {
      seenRunKey.current = runKey;
      setDiscoveredCount(null);
      setRecentFiles([]);
      setCompletedStats(null);
    }
  }, [status, isActive, repositoryId]);

  const handleEvent = useCallback((event: RepositoryEvent) => {
    if (event.event === "index.files.discovered") {
      setDiscoveredCount(event.data.count);
    } else if (event.event === "index.file.completed") {
      setRecentFiles((prev) =>
        [{ path: event.data.path, status: event.data.status }, ...prev].slice(0, 8),
      );
    } else if (event.event === "index.completed") {
      setCompletedStats(event.data);
    }
  }, []);

  useRepositoryEvents(repositoryId, isActive, handleEvent);

  let stage: IndexingStage = "connecting";
  if (status === "failed") stage = "failed";
  else if (status === "ready") stage = "ready";
  else if (status === "pending" || status === "queued") stage = "connecting";
  else if (status === "cloning") stage = "fetching";
  else if (status === "indexing") stage = discoveredCount === null ? "fetching" : "discovering";
  if (status === "indexing" && recentFiles.length > 0) stage = "processing";

  return {
    statusQuery,
    stage,
    discoveredCount,
    completedCount: recentFiles.length,
    recentFiles,
    completedStats,
    isActive,
  };
}
