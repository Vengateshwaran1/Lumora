import { CircleDot } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { RepositorySelect } from "@/components/repository-select";
import { useRepositories } from "@/shared/api/repositories";

import { IssueList } from "./issue-list";

export function IssuesPage() {
  const reposQuery = useRepositories();
  const repos = reposQuery.data ?? [];
  const [searchParams, setSearchParams] = useSearchParams();
  const repositoryId = searchParams.get("repo");

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Issues</h1>
        <p className="text-muted-foreground text-sm">
          Issue sync and issue → implementation plan generation.
        </p>
      </div>

      {repos.length === 0 ? (
        <div className="border-border flex flex-col items-center gap-2 rounded-lg border border-dashed py-16 text-center">
          <CircleDot className="text-muted-foreground size-8" />
          <p className="text-foreground text-sm font-medium">No repositories connected</p>
          <p className="text-muted-foreground max-w-sm text-xs">
            <Link to="/app/repositories" className="text-primary underline">
              Connect a repository
            </Link>{" "}
            before syncing and planning against its issues.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <RepositorySelect
            value={repositoryId}
            onChange={(id) => setSearchParams({ repo: id })}
            placeholder="Choose a repository"
          />
          {repositoryId ? (
            <IssueList repositoryId={repositoryId} />
          ) : (
            <p className="text-muted-foreground text-sm">Select a repository to view its issues.</p>
          )}
        </div>
      )}
    </div>
  );
}
