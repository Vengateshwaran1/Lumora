import { useQuery } from "@tanstack/react-query";
import { Activity, Bot, CircleDot, GitPullRequest, ShieldCheck, Webhook } from "lucide-react";

import { PreviewBadge } from "@/shared/components/preview-badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { listMockActivity } from "@/shared/mocks/api";
import type { ActivityEventType } from "@/shared/mocks/types";

const TYPE_ICON: Record<ActivityEventType, typeof Activity> = {
  index: Activity,
  issue: CircleDot,
  pull_request: GitPullRequest,
  agent_run: Bot,
  webhook: Webhook,
  review: ShieldCheck,
};

export function ActivityPage() {
  const activityQuery = useQuery({ queryKey: ["mock", "activity"], queryFn: listMockActivity });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Activity</h1>
          <p className="text-muted-foreground text-sm">
            Engineering has a memory — code, commits, issues, PRs, and decisions, connected.
          </p>
        </div>
        <PreviewBadge />
      </div>

      <ol className="border-border relative flex flex-col gap-5 border-l pl-6">
        {activityQuery.isLoading
          ? Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-14 rounded-lg" />
            ))
          : activityQuery.data?.map((event) => {
              const Icon = TYPE_ICON[event.type];
              return (
                <li key={event.id} className="relative">
                  <span className="border-background bg-muted absolute top-0.5 -left-[1.85rem] flex size-5 items-center justify-center rounded-full border-2">
                    <Icon className="text-muted-foreground size-3" />
                  </span>
                  <p className="text-sm font-medium">{event.title}</p>
                  <p className="text-muted-foreground text-xs">{event.description}</p>
                  <p className="text-muted-foreground mt-0.5 text-[11px]">
                    {event.repository} · {event.actor} ·{" "}
                    {new Date(event.timestamp).toLocaleString()}
                  </p>
                </li>
              );
            })}
      </ol>
    </div>
  );
}
