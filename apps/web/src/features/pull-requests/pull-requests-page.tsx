import { useQuery } from "@tanstack/react-query";
import { GitPullRequest } from "lucide-react";
import { Link } from "react-router-dom";

import { PreviewBadge } from "@/shared/components/preview-badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { listMockPullRequests } from "@/shared/mocks/api";
import { PrStatusBadge } from "@/shared/mocks/badges";

export function PullRequestsPage() {
  const prQuery = useQuery({ queryKey: ["mock", "pull-requests"], queryFn: listMockPullRequests });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Pull Requests</h1>
          <p className="text-muted-foreground text-sm">Agent-authored and human pull requests.</p>
        </div>
        <PreviewBadge />
      </div>

      <div className="flex flex-col gap-2">
        {prQuery.isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-lg" />
            ))
          : prQuery.data?.map((pr) => (
              <Link
                key={pr.id}
                to={`/app/pull-requests/${pr.id}`}
                className="surface-card-interactive flex flex-col gap-1.5 p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="flex items-center gap-1.5 text-sm font-medium">
                    <GitPullRequest className="size-3.5" />
                    <span className="text-muted-foreground font-normal">#{pr.number}</span>{" "}
                    {pr.title}
                  </p>
                  <PrStatusBadge status={pr.status} />
                </div>
                <div className="text-muted-foreground flex items-center gap-3 text-xs">
                  <span className="font-mono">{pr.branch}</span>
                  <span>·</span>
                  <span>{pr.author === "agent" ? "Coding Agent" : "human"}</span>
                  <span>·</span>
                  <span>
                    +{pr.additions} -{pr.deletions}
                  </span>
                  <span>·</span>
                  <span>
                    {pr.checks.passed}/{pr.checks.passed + pr.checks.failed + pr.checks.pending}{" "}
                    checks
                  </span>
                </div>
              </Link>
            ))}
      </div>
    </div>
  );
}
