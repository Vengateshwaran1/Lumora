import { useMutation, useQuery } from "@tanstack/react-query";
import { Bot, Loader2 } from "lucide-react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

import { generatePlan, getIssue } from "@/shared/api/issues";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";

import { IssueStateBadge } from "./issue-status-badge";

export function IssueDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const repositoryId = searchParams.get("repo");
  const navigate = useNavigate();

  const issueQuery = useQuery({
    queryKey: ["repository", repositoryId, "issue", id],
    queryFn: () => getIssue(repositoryId!, id!),
    enabled: !!repositoryId && !!id,
  });

  const planMutation = useMutation({
    mutationFn: () => generatePlan(repositoryId!, id!),
    onSuccess: (data) => {
      toast.success("Plan generation started");
      void navigate(`/app/runs/${data.run_id}`);
    },
    onError: (error) => toast.error(error.message),
  });

  if (!repositoryId) {
    return (
      <div className="flex max-w-3xl flex-col gap-4">
        <p className="text-muted-foreground text-sm">
          Missing repository context for this issue.{" "}
          <Link to="/app/issues" className="text-primary underline">
            Go back to Issues
          </Link>{" "}
          and open it from there.
        </p>
      </div>
    );
  }

  if (issueQuery.isPending) return <Skeleton className="h-64 rounded-lg" />;
  if (issueQuery.isError)
    return <p className="text-destructive text-sm">{issueQuery.error.message}</p>;

  const issue = issueQuery.data;

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div>
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-2xl font-semibold tracking-tight">
            <span className="text-muted-foreground font-normal">#{issue.number}</span> {issue.title}
          </h1>
          <IssueStateBadge state={issue.state} />
        </div>
        <div className="text-muted-foreground mt-2 flex items-center gap-3 text-xs">
          <span>opened by {issue.author ?? "unknown author"}</span>
          {issue.github_created_at ? (
            <>
              <span>·</span>
              <span>{new Date(issue.github_created_at).toLocaleDateString()}</span>
            </>
          ) : null}
        </div>
      </div>

      {issue.body ? (
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{issue.body}</p>
      ) : (
        <p className="text-muted-foreground text-sm italic">No description.</p>
      )}

      {issue.labels.length > 0 ? (
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
      ) : null}

      <div className="surface-card p-4">
        <div className="flex items-center gap-2">
          <Bot className="text-ai-activity size-4" />
          <p className="text-sm font-medium">Generate implementation plan</p>
        </div>
        <p className="text-muted-foreground mt-1 text-xs">
          The Planning Agent turns this issue into a structured plan — context, dependencies, and
          proposed changes — for human review before any code is written.
        </p>
        <Button
          variant="secondary"
          size="sm"
          className="mt-3"
          onClick={() => planMutation.mutate()}
          disabled={planMutation.isPending}
        >
          {planMutation.isPending ? <Loader2 className="size-3.5 animate-spin" /> : null}
          Generate plan
        </Button>
      </div>

      <a
        href={issue.html_url}
        target="_blank"
        rel="noreferrer"
        className="text-muted-foreground hover:text-foreground text-xs underline"
      >
        View on GitHub
      </a>

      <Link
        to={`/app/issues?repo=${repositoryId}`}
        className="text-muted-foreground hover:text-foreground text-xs underline"
      >
        Back to issues
      </Link>
    </div>
  );
}
