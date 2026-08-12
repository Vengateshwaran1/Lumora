import { useQuery } from "@tanstack/react-query";
import { Activity, CircleDot, FileCode2, GitPullRequest, Layers, Network } from "lucide-react";
import { useParams, useSearchParams } from "react-router-dom";

import { getIndexStatus } from "@/shared/api/repositories";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";

import { SearchPanel } from "@/components/knowledge/search-panel";
import { RepoStatusBadge } from "../repo-status-badge";
import { MockTab } from "./mock-tab";
import { OverviewTab } from "./overview-tab";

const TABS = [
  { value: "overview", label: "Overview" },
  { value: "knowledge", label: "Knowledge" },
  { value: "files", label: "Files" },
  { value: "symbols", label: "Symbols" },
  { value: "dependencies", label: "Dependencies" },
  { value: "issues", label: "Issues" },
  { value: "pull-requests", label: "Pull Requests" },
  { value: "activity", label: "Activity" },
] as const;

export function RepositoryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get("tab") ?? "overview";

  const statusQuery = useQuery({
    queryKey: ["repository", id, "index-status"],
    queryFn: () => getIndexStatus(id!),
    enabled: !!id,
  });

  if (!id) return null;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {statusQuery.data?.name ?? "Repository"}
          </h1>
          <p className="text-muted-foreground text-sm break-all">{statusQuery.data?.url}</p>
        </div>
        {statusQuery.data ? <RepoStatusBadge status={statusQuery.data.status} /> : null}
      </div>

      <Tabs value={tab} onValueChange={(value) => setSearchParams({ tab: value })}>
        <TabsList className="w-full justify-start overflow-x-auto">
          {TABS.map((entry) => (
            <TabsTrigger key={entry.value} value={entry.value}>
              {entry.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab repositoryId={id} />
        </TabsContent>
        <TabsContent value="knowledge">
          <SearchPanel repositoryId={id} />
        </TabsContent>
        <TabsContent value="files">
          <MockTab
            icon={FileCode2}
            title="Files"
            description="A full repository file tree with per-file indexing detail arrives with the Code Explorer in a later milestone."
          />
        </TabsContent>
        <TabsContent value="symbols">
          <MockTab
            icon={Layers}
            title="Symbols"
            description="Browsable symbol index (functions, classes, types) beyond search results arrives in a later milestone."
          />
        </TabsContent>
        <TabsContent value="dependencies">
          <MockTab
            icon={Network}
            title="Dependencies"
            description="Interactive dependency graph across files and packages arrives in a later milestone."
          />
        </TabsContent>
        <TabsContent value="issues">
          <MockTab
            icon={CircleDot}
            title="Issues"
            description="Issue sync and issue-to-plan generation arrive with the Planning Agent (M3)."
          />
        </TabsContent>
        <TabsContent value="pull-requests">
          <MockTab
            icon={GitPullRequest}
            title="Pull Requests"
            description="Agent-authored pull requests arrive with PR automation (M5)."
          />
        </TabsContent>
        <TabsContent value="activity">
          <MockTab
            icon={Activity}
            title="Activity"
            description="A durable per-repository activity log arrives alongside the agent and PR milestones."
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
