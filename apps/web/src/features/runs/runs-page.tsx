import { useQuery } from "@tanstack/react-query";
import { Bot } from "lucide-react";
import { Link } from "react-router-dom";

import { PreviewBadge } from "@/shared/components/preview-badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { listMockAgentRuns } from "@/shared/mocks/api";
import { RunStatusBadge } from "@/shared/mocks/badges";

export function RunsPage() {
  const runsQuery = useQuery({ queryKey: ["mock", "agent-runs"], queryFn: listMockAgentRuns });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Agent Runs</h1>
          <p className="text-muted-foreground text-sm">
            Supervisor → Planner → Retriever → Coder → Tester → Debugger → Reviewer.
          </p>
        </div>
        <PreviewBadge />
      </div>

      <div className="flex flex-col gap-2">
        {runsQuery.isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-lg" />
            ))
          : runsQuery.data?.map((run) => (
              <Link
                key={run.id}
                to={`/app/runs/${run.id}`}
                className="surface-card-interactive flex flex-col gap-1.5 p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="flex items-center gap-1.5 text-sm font-medium">
                    <Bot className="size-3.5" />
                    {run.repository}
                  </p>
                  <RunStatusBadge status={run.status} />
                </div>
                <div className="text-muted-foreground flex items-center gap-3 text-xs">
                  <span>{run.currentAgent ? `Current: ${run.currentAgent}` : "Finished"}</span>
                  <span>·</span>
                  <span>started {new Date(run.startedAt).toLocaleString()}</span>
                </div>
              </Link>
            ))}
      </div>
    </div>
  );
}
