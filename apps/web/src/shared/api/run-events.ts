import { useEffect } from "react";

import type { RunEvent } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

/** Subscribes to the run SSE stream for live decoration on top of the
 * `GET /runs/{id}` poll (which stays the source of truth — there is no rich,
 * fully-enumerated event union for runs yet, unlike the repository stream:
 * in practice only `"run.queued"` fires, published at enqueue time). Same
 * fire-and-forget caveats as `shared/api/events.ts::useRepositoryEvents` —
 * no replay for events published before the connection opens. `onEvent`
 * fires directly from the SSE callback — callers should update their own
 * state there (stable via `useCallback`) rather than deriving it in a
 * separate effect. */
export function useRunEvents(
  runId: string | undefined,
  enabled: boolean,
  onEvent: (event: RunEvent) => void,
) {
  useEffect(() => {
    if (!runId || !enabled) return;

    const source = new EventSource(`${API_BASE_URL}/runs/${runId}/stream`);

    source.onmessage = (message) => {
      try {
        const parsed = JSON.parse(message.data as string) as RunEvent;
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
  }, [runId, enabled]);
}
