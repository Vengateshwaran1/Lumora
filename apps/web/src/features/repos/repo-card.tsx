import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ACTIVE_STATUSES, getIndexStatus, triggerReindex } from "./api";
import { RepoStatusBadge } from "./repo-status-badge";
import { useReposStore } from "./store";

function formatTimestamp(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

export function RepoCard({ repositoryId }: { repositoryId: string }) {
  const queryClient = useQueryClient();
  const removeTracked = useReposStore((state) => state.removeTracked);

  const statusQuery = useQuery({
    queryKey: ["repository", repositoryId, "index-status"],
    queryFn: () => getIndexStatus(repositoryId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ACTIVE_STATUSES.includes(status) ? 2000 : false;
    },
  });

  const reindexMutation = useMutation({
    mutationFn: () => triggerReindex(repositoryId),
    onSuccess: (data) => {
      queryClient.setQueryData(["repository", repositoryId, "index-status"], data);
    },
  });

  if (statusQuery.isPending) {
    return (
      <div className="border-border bg-card rounded-lg border p-4 text-sm">Loading repository…</div>
    );
  }

  if (statusQuery.isError) {
    return (
      <div className="border-border bg-card rounded-lg border p-4">
        <p className="text-destructive text-sm">
          Couldn't load this repository ({statusQuery.error.message}).
        </p>
        <button
          type="button"
          onClick={() => removeTracked(repositoryId)}
          className="text-muted-foreground hover:text-foreground mt-2 text-xs underline"
        >
          Remove from list
        </button>
      </div>
    );
  }

  const repo = statusQuery.data;
  const isActive = ACTIVE_STATUSES.includes(repo.status);

  return (
    <div className="border-border bg-card rounded-lg border p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-medium">{repo.name}</p>
          <p className="text-muted-foreground text-xs break-all">{repo.url}</p>
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

      <div className="mt-4 flex items-center gap-3">
        <button
          type="button"
          onClick={() => reindexMutation.mutate()}
          disabled={isActive || reindexMutation.isPending}
          className="bg-primary text-primary-foreground rounded-md px-3 py-1.5 text-xs font-medium disabled:opacity-50"
        >
          {isActive ? "Indexing…" : "Re-index"}
        </button>
        <button
          type="button"
          onClick={() => removeTracked(repositoryId)}
          className="text-muted-foreground hover:text-foreground text-xs underline"
        >
          Remove from list
        </button>
      </div>
    </div>
  );
}
