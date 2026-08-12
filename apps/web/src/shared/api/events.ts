import { useEffect } from "react";

import type { RepositoryEvent } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

/** Subscribes to the repository SSE stream for live deltas on top of the
 * `/index-status` poll (which stays the source of truth — see
 * `application/jobs/events.py`: this is fire-and-forget, no replay for
 * events published before the connection opens). `onEvent` fires directly
 * from the SSE callback — callers should update their own state there
 * (stable via `useCallback`) rather than deriving it in a separate effect. */
export function useRepositoryEvents(
  repositoryId: string | undefined,
  enabled: boolean,
  onEvent: (event: RepositoryEvent) => void,
) {
  useEffect(() => {
    if (!repositoryId || !enabled) return;

    const source = new EventSource(`${API_BASE_URL}/repositories/${repositoryId}/events`);

    source.onmessage = (message) => {
      try {
        const parsed = JSON.parse(message.data as string) as RepositoryEvent;
        onEvent(parsed);
      } catch {
        // Malformed/partial message — ignore, polling remains authoritative.
      }
    };

    source.onerror = () => {
      // EventSource auto-reconnects; polling is the durable fallback so we
      // don't need custom retry logic here.
    };

    return () => source.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- onEvent must be a stable useCallback from the caller; including it would resubscribe every render.
  }, [repositoryId, enabled]);
}
