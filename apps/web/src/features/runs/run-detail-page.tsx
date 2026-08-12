import { useQuery } from "@tanstack/react-query";
import { Check, Loader2 } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { PreviewBadge } from "@/shared/components/preview-badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { getMockAgentRun } from "@/shared/mocks/api";
import { RunStatusBadge } from "@/shared/mocks/badges";
import { cn } from "@/shared/lib/utils";

export function RunDetailPage() {
  const { id } = useParams<{ id: string }>();
  const runQuery = useQuery({
    queryKey: ["mock", "agent-run", id],
    queryFn: () => getMockAgentRun(id!),
    enabled: !!id,
  });

  if (runQuery.isLoading) return <Skeleton className="h-96 rounded-lg" />;
  if (!runQuery.data) return <p className="text-muted-foreground text-sm">Run not found.</p>;

  const run = runQuery.data;

  return (
    <div className="flex max-w-2xl flex-col gap-6">
      <PreviewBadge />
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{run.repository}</h1>
          <p className="text-muted-foreground text-sm">
            Started {new Date(run.startedAt).toLocaleString()}
          </p>
        </div>
        <RunStatusBadge status={run.status} />
      </div>

      <ol className="flex flex-col gap-0">
        {run.steps.map((step, index) => (
          <li key={step.name} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex size-6 items-center justify-center rounded-full border text-xs",
                  step.status === "done" && "bg-success border-success text-success-foreground",
                  step.status === "active" && "border-ai-activity text-ai-activity",
                  step.status === "pending" && "border-border text-muted-foreground",
                  step.status === "failed" && "bg-destructive border-destructive text-white",
                )}
              >
                {step.status === "done" ? (
                  <Check className="size-3.5" />
                ) : step.status === "active" ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  index + 1
                )}
              </div>
              {index < run.steps.length - 1 ? (
                <div
                  className={cn("w-px flex-1", step.status === "done" ? "bg-success" : "bg-border")}
                />
              ) : null}
            </div>
            <div className="flex-1 pb-6">
              <p
                className={cn(
                  "text-sm font-medium",
                  step.status === "active" && "text-ai-activity",
                  step.status === "pending" && "text-muted-foreground",
                )}
              >
                {step.name}
              </p>
              {step.startedAt ? (
                <p className="text-muted-foreground text-xs">
                  {new Date(step.startedAt).toLocaleTimeString()}
                  {step.completedAt
                    ? ` – ${new Date(step.completedAt).toLocaleTimeString()}`
                    : " – in progress"}
                </p>
              ) : null}
            </div>
          </li>
        ))}
      </ol>

      {run.status === "awaiting_approval" ? (
        <div className="border-approval/30 bg-approval/5 rounded-lg border p-4">
          <p className="text-approval text-sm font-medium">Awaiting human approval</p>
          <p className="text-muted-foreground mt-1 text-xs">
            Autonomous does not mean uncontrolled — a human reviews and approves before this run
            opens a pull request. Approval actions arrive with M4.
          </p>
        </div>
      ) : null}

      <Link
        to="/app/runs"
        className="text-muted-foreground hover:text-foreground text-xs underline"
      >
        Back to agent runs
      </Link>
    </div>
  );
}
