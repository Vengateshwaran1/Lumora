import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CircleDot, Loader2, RefreshCw } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { syncIssues } from "@/shared/api/issues";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";

import { IssueStateBadge } from "./issue-status-badge";
import { useIssues } from "./use-issues";

/** Repo-scoped issues list — used both by the top-level `/app/issues` page
 * (after a repository is picked) and the repository detail page's Issues
 * tab (already scoped, no picker needed). */
export function IssueList({ repositoryId }: { repositoryId: string }) {
  const queryClient = useQueryClient();
  const issuesQuery = useIssues(repositoryId);

  const syncMutation = useMutation({
    mutationFn: () => syncIssues(repositoryId),
    onSuccess: () => {
      toast.success("Issue sync started");
      // Sync runs as a backend BackgroundTask with no completion signal this
      // milestone (no polling/SSE endpoint for it yet) — a short delay before
      // invalidating is the best available approximation of "probably done".
      setTimeout(() => {
        void queryClient.invalidateQueries({ queryKey: ["repository", repositoryId, "issues"] });
      }, 1500);
    },
    onError: (error) => toast.error(error.message),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground text-xs">
          Synced from GitHub. Re-sync to pull in new or updated issues.
        </p>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
        >
          {syncMutation.isPending ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <RefreshCw className="size-3.5" />
          )}
          Sync issues
        </Button>
      </div>

      <div className="flex flex-col gap-2">
        {issuesQuery.isPending ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-lg" />)
        ) : issuesQuery.isError ? (
          <p className="text-destructive text-sm">{issuesQuery.error.message}</p>
        ) : issuesQuery.data.length === 0 ? (
          <div className="border-border flex flex-col items-center gap-2 rounded-lg border border-dashed py-16 text-center">
            <CircleDot className="text-muted-foreground size-8" />
            <p className="text-foreground text-sm font-medium">No issues synced yet</p>
            <p className="text-muted-foreground max-w-sm text-xs">
              Sync to pull open and closed issues from this repository's GitHub remote.
            </p>
          </div>
        ) : (
          issuesQuery.data.map((issue) => (
            <Link
              key={issue.id}
              to={`/app/issues/${issue.id}?repo=${repositoryId}`}
              className="surface-card-interactive flex flex-col gap-1.5 p-4"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="min-w-0 truncate text-sm font-medium">
                  <span className="text-muted-foreground font-normal">#{issue.number}</span>{" "}
                  {issue.title}
                </p>
                <IssueStateBadge state={issue.state} />
              </div>
              <div className="text-muted-foreground flex items-center gap-3 text-xs">
                {issue.labels.length > 0 ? <span>{issue.labels.join(", ")}</span> : null}
                {issue.labels.length > 0 ? <span>·</span> : null}
                <span>{issue.author ?? "unknown author"}</span>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
