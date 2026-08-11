import { cn } from "@/shared/lib/utils";

import type { RepositoryStatus } from "./api";

const STATUS_LABEL: Record<RepositoryStatus, string> = {
  pending: "Idle",
  queued: "Queued",
  cloning: "Cloning",
  indexing: "Indexing",
  ready: "Ready",
  failed: "Failed",
};

const STATUS_CLASSES: Record<RepositoryStatus, string> = {
  pending: "bg-muted text-muted-foreground",
  queued: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  cloning: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  indexing: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  ready: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  failed: "bg-destructive/15 text-destructive",
};

export function RepoStatusBadge({ status }: { status: RepositoryStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        STATUS_CLASSES[status],
      )}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}
