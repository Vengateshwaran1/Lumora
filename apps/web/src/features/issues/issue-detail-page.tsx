import { useQuery } from "@tanstack/react-query";
import { Bot } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { PreviewBadge } from "@/shared/components/preview-badge";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { getMockIssue } from "@/shared/mocks/api";
import { IssueStatusBadge } from "@/shared/mocks/badges";

export function IssueDetailPage() {
  const { id } = useParams<{ id: string }>();
  const issueQuery = useQuery({
    queryKey: ["mock", "issue", id],
    queryFn: () => getMockIssue(id!),
    enabled: !!id,
  });

  if (issueQuery.isLoading) return <Skeleton className="h-64 rounded-lg" />;
  if (!issueQuery.data) return <p className="text-muted-foreground text-sm">Issue not found.</p>;

  const issue = issueQuery.data;

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div>
        <div className="mb-2 flex items-center gap-2">
          <PreviewBadge />
        </div>
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-2xl font-semibold tracking-tight">
            <span className="text-muted-foreground font-normal">#{issue.number}</span> {issue.title}
          </h1>
          <IssueStatusBadge status={issue.status} />
        </div>
        <div className="text-muted-foreground mt-2 flex items-center gap-3 text-xs">
          <span>{issue.repository}</span>
          <span>·</span>
          <span>{issue.priority} priority</span>
          <span>·</span>
          <span>opened by {issue.author}</span>
        </div>
      </div>

      <p className="text-sm leading-relaxed">{issue.description}</p>

      <div className="flex flex-wrap gap-1.5">
        {issue.labels.map((label) => (
          <span
            key={label}
            className="bg-secondary text-secondary-foreground rounded-full px-2.5 py-0.5 text-xs"
          >
            {label}
          </span>
        ))}
      </div>

      <div className="surface-card p-4">
        <div className="flex items-center gap-2">
          <Bot className="text-ai-activity size-4" />
          <p className="text-sm font-medium">Generate implementation plan</p>
        </div>
        <p className="text-muted-foreground mt-1 text-xs">
          The Planning Agent turns this issue into a structured plan — context, dependencies, and
          proposed changes — for human review before any code is written. Arrives in M3.
        </p>
        <Button variant="secondary" size="sm" disabled className="mt-3">
          Generate plan
        </Button>
      </div>

      <Link
        to="/app/issues"
        className="text-muted-foreground hover:text-foreground text-xs underline"
      >
        Back to issues
      </Link>
    </div>
  );
}
