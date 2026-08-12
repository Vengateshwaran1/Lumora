import { useQueries, useQuery } from "@tanstack/react-query";
import { Activity, FolderGit2, MessageSquare, Search } from "lucide-react";
import { Link } from "react-router-dom";

import { Reveal } from "@/components/motion/reveal";
import { useReposStore } from "@/features/repos/store";
import { getIndexStatus } from "@/shared/api/repositories";
import { ACTIVE_STATUSES } from "@/shared/api/types";
import { PreviewBadge } from "@/shared/components/preview-badge";
import { listMockActivity } from "@/shared/mocks/api";

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  icon: typeof FolderGit2;
}) {
  return (
    <div className="surface-card p-4">
      <div className="text-muted-foreground flex items-center gap-2 text-xs">
        <Icon className="size-3.5" />
        {label}
      </div>
      <p className="mt-2 text-2xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}

export function DashboardPage() {
  const tracked = useReposStore((state) => state.tracked);
  const statusResults = useQueries({
    queries: tracked.map((repo) => ({
      queryKey: ["repository", repo.id, "index-status"],
      queryFn: () => getIndexStatus(repo.id),
    })),
  });
  const activityQuery = useQuery({ queryKey: ["mock", "activity"], queryFn: listMockActivity });

  const ready = statusResults.filter((r) => r.data?.status === "ready").length;
  const active = statusResults.filter(
    (r) => r.data && ACTIVE_STATUSES.includes(r.data.status),
  ).length;
  const totalChunks = statusResults.reduce((sum, r) => sum + (r.data?.indexed_chunk_count ?? 0), 0);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Overview</h1>
        <p className="text-muted-foreground text-sm">Your engineering intelligence at a glance.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Repositories" value={tracked.length} icon={FolderGit2} />
        <StatCard label="Ready" value={ready} icon={Activity} />
        <StatCard label="Indexing" value={active} icon={Activity} />
        <StatCard label="Indexed chunks" value={totalChunks} icon={Search} />
      </div>

      {tracked.length === 0 ? (
        <Reveal>
          <div className="border-border flex flex-col items-center gap-3 rounded-lg border border-dashed py-16 text-center">
            <FolderGit2 className="text-muted-foreground size-8" />
            <p className="text-foreground text-sm font-medium">Connect your first repository</p>
            <p className="text-muted-foreground max-w-sm text-xs">
              Lumora will clone, index, and build a searchable knowledge base you can query and chat
              with.
            </p>
            <Link
              to="/app/repositories"
              className="bg-primary text-primary-foreground rounded-md px-3 py-1.5 text-sm font-medium"
            >
              Connect a repository
            </Link>
          </div>
        </Reveal>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Reveal>
            <Link to="/app/knowledge" className="surface-card-interactive flex flex-col gap-1 p-4">
              <Search className="text-primary size-4" />
              <p className="text-sm font-medium">Search your knowledge base</p>
              <p className="text-muted-foreground text-xs">Hybrid retrieval with citations.</p>
            </Link>
          </Reveal>
          <Reveal delay={0.03}>
            <Link to="/app/chat" className="surface-card-interactive flex flex-col gap-1 p-4">
              <MessageSquare className="text-primary size-4" />
              <p className="text-sm font-medium">Ask Lumora a question</p>
              <p className="text-muted-foreground text-xs">
                Investigate your codebase conversationally.
              </p>
            </Link>
          </Reveal>
        </div>
      )}

      <div>
        <div className="mb-2 flex items-center gap-2">
          <h2 className="text-sm font-medium">Recent activity</h2>
          <PreviewBadge />
        </div>
        <div className="flex flex-col gap-2">
          {(activityQuery.data ?? []).slice(0, 5).map((event) => (
            <div key={event.id} className="surface-card p-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">{event.title}</p>
                <span className="text-muted-foreground text-[11px]">
                  {new Date(event.timestamp).toLocaleDateString()}
                </span>
              </div>
              <p className="text-muted-foreground mt-0.5 text-xs">{event.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
