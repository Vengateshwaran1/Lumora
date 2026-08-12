import { FolderGit2 } from "lucide-react";

import { Reveal } from "@/components/motion/reveal";

import { ConnectRepoForm } from "./connect-repo-form";
import { RepoCard } from "./repo-card";
import { useReposStore } from "./store";

export function ReposPage() {
  const tracked = useReposStore((state) => state.tracked);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Repositories</h1>
        <p className="text-muted-foreground text-sm">
          Connect a repository and monitor its indexing status. Pushes are indexed incrementally via
          a GitHub webhook once configured.
        </p>
      </div>

      <ConnectRepoForm />

      {tracked.length === 0 ? (
        <div className="border-border flex flex-col items-center gap-2 rounded-lg border border-dashed py-16 text-center">
          <FolderGit2 className="text-muted-foreground size-8" />
          <p className="text-foreground text-sm font-medium">No repositories connected yet</p>
          <p className="text-muted-foreground max-w-sm text-xs">
            Paste a Git URL above to clone, index, and start asking Lumora questions about it.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {tracked.map((repo, index) => (
            <Reveal key={repo.id} delay={index * 0.03}>
              <RepoCard repositoryId={repo.id} />
            </Reveal>
          ))}
        </div>
      )}
    </div>
  );
}
