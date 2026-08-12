import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { PreviewBadge } from "@/shared/components/preview-badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { IssueStatusBadge } from "@/shared/mocks/badges";
import { listMockIssues } from "@/shared/mocks/api";

export function IssuesPage() {
  const issuesQuery = useQuery({ queryKey: ["mock", "issues"], queryFn: listMockIssues });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Issues</h1>
          <p className="text-muted-foreground text-sm">
            Issue sync and issue → implementation plan generation.
          </p>
        </div>
        <PreviewBadge />
      </div>

      <div className="flex flex-col gap-2">
        {issuesQuery.isLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-lg" />
            ))
          : issuesQuery.data?.map((issue) => (
              <Link
                key={issue.id}
                to={`/app/issues/${issue.id}`}
                className="surface-card-interactive flex flex-col gap-1.5 p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">
                    <span className="text-muted-foreground font-normal">#{issue.number}</span>{" "}
                    {issue.title}
                  </p>
                  <IssueStatusBadge status={issue.status} />
                </div>
                <div className="text-muted-foreground flex items-center gap-3 text-xs">
                  <span>{issue.repository}</span>
                  <span>·</span>
                  <span>{issue.priority} priority</span>
                  <span>·</span>
                  <span>{issue.author}</span>
                </div>
              </Link>
            ))}
      </div>
    </div>
  );
}
