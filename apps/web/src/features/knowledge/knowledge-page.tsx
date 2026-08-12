import { Search } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { SearchPanel } from "@/components/knowledge/search-panel";
import { RepositorySelect } from "@/components/repository-select";
import { useReposStore } from "@/features/repos/store";

export function KnowledgePage() {
  const tracked = useReposStore((state) => state.tracked);
  const [searchParams, setSearchParams] = useSearchParams();
  const repositoryId = searchParams.get("repo");

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Knowledge</h1>
        <p className="text-muted-foreground text-sm">
          Hybrid dense + BM25 retrieval with reranking over your indexed codebase, with citations.
        </p>
      </div>

      {tracked.length === 0 ? (
        <div className="border-border flex flex-col items-center gap-2 rounded-lg border border-dashed py-16 text-center">
          <Search className="text-muted-foreground size-8" />
          <p className="text-foreground text-sm font-medium">No repositories connected</p>
          <p className="text-muted-foreground max-w-sm text-xs">
            <Link to="/app/repositories" className="text-primary underline">
              Connect a repository
            </Link>{" "}
            and index it before searching its knowledge base.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <RepositorySelect
            value={repositoryId}
            onChange={(id) => setSearchParams({ repo: id })}
            placeholder="Choose a repository to search"
          />
          {repositoryId ? (
            <SearchPanel repositoryId={repositoryId} />
          ) : (
            <p className="text-muted-foreground text-sm">Select a repository to begin.</p>
          )}
        </div>
      )}
    </div>
  );
}
