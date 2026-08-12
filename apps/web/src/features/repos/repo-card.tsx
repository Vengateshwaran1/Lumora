import { useMutation, useQueryClient } from "@tanstack/react-query";
import { MessageSquare, RefreshCw } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { triggerIndex, triggerReindex } from "@/shared/api/repositories";
import { ACTIVE_STATUSES } from "@/shared/api/types";
import { Button } from "@/shared/components/ui/button";
import { Card } from "@/shared/components/ui/card";

import { useIndexingProgress } from "@/components/indexing/use-indexing-progress";
import { RepoStatusBadge } from "./repo-status-badge";

function formatTimestamp(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

export function RepoCard({ repositoryId }: { repositoryId: string }) {
  const queryClient = useQueryClient();
  const { statusQuery } = useIndexingProgress(repositoryId);

  const indexMutation = useMutation({
    mutationFn: () => triggerIndex(repositoryId),
    onSuccess: (data) => {
      queryClient.setQueryData(["repository", repositoryId, "index-status"], data);
    },
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

  if (statusQuery.isPending) {
    return <Card className="text-muted-foreground p-4 text-sm">Loading repository…</Card>;
  }

  if (statusQuery.isError) {
    return (
      <Card className="p-4">
        <p className="text-destructive text-sm">
          Couldn't load this repository ({statusQuery.error.message}).
        </p>
      </Card>
    );
  }

  const repo = statusQuery.data;
  const isActive = ACTIVE_STATUSES.includes(repo.status);
  const neverIndexed = repo.status === "pending";

  return (
    <Card className="hover:border-border-strong group p-4 transition-all duration-200 ease-[var(--ease-premium)] hover:shadow-[var(--shadow-card-hover)]">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <Link to={`/app/repositories/${repositoryId}`} className="hover:text-primary font-medium">
            {repo.name}
          </Link>
          <p className="text-muted-foreground truncate text-xs">{repo.url}</p>
        </div>
        <RepoStatusBadge status={repo.status} />
      </div>

      <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <dt className="text-muted-foreground">Last indexed commit</dt>
        <dd className="font-mono">
          {repo.last_indexed_commit ? repo.last_indexed_commit.slice(0, 12) : "—"}
        </dd>

        <dt className="text-muted-foreground">Last successful index</dt>
        <dd>{repo.status === "ready" ? formatTimestamp(repo.index_completed_at) : "—"}</dd>

        <dt className="text-muted-foreground">Indexed files / chunks</dt>
        <dd>
          {repo.indexed_file_count} / {repo.indexed_chunk_count}
        </dd>
      </dl>

      {repo.status === "failed" && repo.error_message ? (
        <p className="bg-destructive/10 text-destructive mt-3 rounded-md px-3 py-2 text-xs">
          {repo.error_message}
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button variant="secondary" size="sm" asChild>
          <Link to={`/app/repositories/${repositoryId}`}>Open</Link>
        </Button>
        <Button variant="secondary" size="sm" asChild>
          <Link to={`/app/chat?repo=${repositoryId}`}>
            <MessageSquare className="size-3.5" />
            Ask Lumora
          </Link>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => (neverIndexed ? indexMutation.mutate() : reindexMutation.mutate())}
          disabled={isActive || indexMutation.isPending || reindexMutation.isPending}
        >
          <RefreshCw className={`size-3.5 ${isActive ? "animate-spin" : ""}`} />
          {isActive ? "Indexing…" : neverIndexed ? "Index now" : "Re-index"}
        </Button>
      </div>
    </Card>
  );
}
