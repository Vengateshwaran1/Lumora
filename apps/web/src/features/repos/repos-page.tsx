import { ConnectRepoForm } from "./connect-repo-form";
import { RepoCard } from "./repo-card";
import { useReposStore } from "./store";

export function ReposPage() {
  const tracked = useReposStore((state) => state.tracked);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Repos</h1>
        <p className="text-muted-foreground text-sm">
          Connect a repository and monitor its indexing status. Pushes are indexed incrementally via
          a GitHub webhook once configured — see the setup docs.
        </p>
      </div>

      <ConnectRepoForm />

      {tracked.length === 0 ? (
        <p className="text-muted-foreground text-sm">No repositories connected yet.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {tracked.map((repo) => (
            <RepoCard key={repo.id} repositoryId={repo.id} />
          ))}
        </div>
      )}
    </div>
  );
}
