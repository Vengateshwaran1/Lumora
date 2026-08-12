import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, CircleDashed, XCircle } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { PreviewBadge } from "@/shared/components/preview-badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { getMockPullRequest } from "@/shared/mocks/api";
import { PrStatusBadge } from "@/shared/mocks/badges";

export function PullRequestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const prQuery = useQuery({
    queryKey: ["mock", "pull-request", id],
    queryFn: () => getMockPullRequest(id!),
    enabled: !!id,
  });

  if (prQuery.isLoading) return <Skeleton className="h-64 rounded-lg" />;
  if (!prQuery.data)
    return <p className="text-muted-foreground text-sm">Pull request not found.</p>;

  const pr = prQuery.data;

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <PreviewBadge />
      <div>
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-2xl font-semibold tracking-tight">
            <span className="text-muted-foreground font-normal">#{pr.number}</span> {pr.title}
          </h1>
          <PrStatusBadge status={pr.status} />
        </div>
        <div className="text-muted-foreground mt-2 flex items-center gap-3 font-mono text-xs">
          <span>{pr.branch}</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="surface-card p-3">
          <p className="text-muted-foreground text-[11px] tracking-wide uppercase">Files changed</p>
          <p className="mt-1 text-sm font-semibold">{pr.filesChanged}</p>
        </div>
        <div className="surface-card p-3">
          <p className="text-muted-foreground text-[11px] tracking-wide uppercase">Additions</p>
          <p className="text-success mt-1 text-sm font-semibold">+{pr.additions}</p>
        </div>
        <div className="surface-card p-3">
          <p className="text-muted-foreground text-[11px] tracking-wide uppercase">Deletions</p>
          <p className="text-destructive mt-1 text-sm font-semibold">-{pr.deletions}</p>
        </div>
      </div>

      <div>
        <h2 className="mb-2 text-sm font-medium">Checks</h2>
        <div className="surface-card flex items-center gap-6 p-4">
          <span className="text-success flex items-center gap-1.5 text-sm">
            <CheckCircle2 className="size-4" /> {pr.checks.passed} passed
          </span>
          {pr.checks.failed > 0 ? (
            <span className="text-destructive flex items-center gap-1.5 text-sm">
              <XCircle className="size-4" /> {pr.checks.failed} failed
            </span>
          ) : null}
          {pr.checks.pending > 0 ? (
            <span className="text-muted-foreground flex items-center gap-1.5 text-sm">
              <CircleDashed className="size-4" /> {pr.checks.pending} pending
            </span>
          ) : null}
        </div>
      </div>

      <Link
        to="/app/pull-requests"
        className="text-muted-foreground hover:text-foreground text-xs underline"
      >
        Back to pull requests
      </Link>
    </div>
  );
}
