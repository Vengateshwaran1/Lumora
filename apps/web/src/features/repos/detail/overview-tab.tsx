import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { IndexingPipeline } from "@/components/indexing/indexing-pipeline";
import { IndexingStatsCard } from "@/components/indexing/indexing-stats-card";
import { useIndexingProgress } from "@/components/indexing/use-indexing-progress";
import { triggerIndex, triggerReindex } from "@/shared/api/repositories";
import { ACTIVE_STATUSES } from "@/shared/api/types";
import { Button } from "@/shared/components/ui/button";

function formatTimestamp(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

export function OverviewTab({ repositoryId }: { repositoryId: string }) {
  const queryClient = useQueryClient();
  const { statusQuery, stage, discoveredCount, completedCount, recentFiles, completedStats } =
    useIndexingProgress(repositoryId);

  const indexMutation = useMutation({
    mutationFn: () => triggerIndex(repositoryId),
    onSuccess: (data) =>
      queryClient.setQueryData(["repository", repositoryId, "index-status"], data),
    onError: (error) => toast.error(error.message),
  });

  const reindexMutation = useMutation({
    mutationFn: () => triggerReindex(repositoryId),
    onSuccess: (data) => {
      queryClient.setQueryData(["repository", repositoryId, "index-status"], data);
      toast.success("Re-index queued");
    },
    onError: (error) => toast.error(error.message),
  });

  if (statusQuery.isPending) return <p className="text-muted-foreground text-sm">Loading…</p>;
  if (statusQuery.isError)
    return <p className="text-destructive text-sm">{statusQuery.error.message}</p>;

  const repo = statusQuery.data;
  const isActive = ACTIVE_STATUSES.includes(repo.status);
  const neverIndexed = repo.status === "pending";

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="surface-card p-4">
          <p className="text-muted-foreground text-[11px] tracking-wide uppercase">
            Default branch
          </p>
          <p className="mt-1 font-mono text-sm">{repo.default_branch ?? "—"}</p>
        </div>
        <div className="surface-card p-4">
          <p className="text-muted-foreground text-[11px] tracking-wide uppercase">
            Last indexed commit
          </p>
          <p className="mt-1 font-mono text-sm">
            {repo.last_indexed_commit ? repo.last_indexed_commit.slice(0, 12) : "—"}
          </p>
        </div>
        <div className="surface-card p-4">
          <p className="text-muted-foreground text-[11px] tracking-wide uppercase">Indexed files</p>
          <p className="mt-1 text-sm font-semibold tabular-nums">{repo.indexed_file_count}</p>
        </div>
        <div className="surface-card p-4">
          <p className="text-muted-foreground text-[11px] tracking-wide uppercase">
            Indexed chunks
          </p>
          <p className="mt-1 text-sm font-semibold tabular-nums">{repo.indexed_chunk_count}</p>
        </div>
      </div>

      <div>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-medium">Indexing</h2>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => (neverIndexed ? indexMutation.mutate() : reindexMutation.mutate())}
            disabled={isActive || indexMutation.isPending || reindexMutation.isPending}
          >
            {isActive ? "Indexing…" : neverIndexed ? "Index now" : "Re-index"}
          </Button>
        </div>
        <IndexingPipeline
          stage={stage}
          discoveredCount={discoveredCount}
          completedCount={completedCount}
          recentFiles={recentFiles}
          errorMessage={repo.error_message}
        />
      </div>

      {completedStats ? (
        <IndexingStatsCard stats={completedStats} />
      ) : repo.status === "ready" ? (
        <p className="text-muted-foreground text-xs">
          Last successful index: {formatTimestamp(repo.index_completed_at)}. Per-run stats only
          appear for runs observed live via the events stream.
        </p>
      ) : null}
    </div>
  );
}
