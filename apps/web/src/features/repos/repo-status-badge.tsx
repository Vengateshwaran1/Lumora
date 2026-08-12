import { StatusIndicator, type SignalTone } from "@/components/motion/status-indicator";

import type { RepositoryStatus } from "@/shared/api/types";

const STATUS_LABEL: Record<RepositoryStatus, string> = {
  pending: "Idle",
  queued: "Queued",
  cloning: "Cloning",
  indexing: "Indexing",
  ready: "Ready",
  failed: "Failed",
};

const STATUS_TONE: Record<RepositoryStatus, SignalTone> = {
  pending: "neutral",
  queued: "engineering",
  cloning: "engineering",
  indexing: "engineering",
  ready: "success",
  failed: "error",
};

const ACTIVE: RepositoryStatus[] = ["queued", "cloning", "indexing"];

export function RepoStatusBadge({ status }: { status: RepositoryStatus }) {
  return (
    <StatusIndicator
      tone={STATUS_TONE[status]}
      label={STATUS_LABEL[status]}
      pulse={ACTIVE.includes(status)}
    />
  );
}
